from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from datetime import date
from typing import List, Optional
from uuid import UUID
import uuid

from app.api.deps import get_db 
from app.services.indicador_macro_service import( 
    obtener_indicador_por_fecha, 
    obtener_ultimos_registros, 
    encolar_cosecha_masiva, 
    auditar_indicadores, 
    obtener_serie_tiempo
)
from app.models.indicador_macro import IndicadorMacro
from app.schemas.indicador_macro import IndicadorMacroCreate, IndicadorMacroResponse, CosechaMasivaRequest

router = APIRouter()

# ====================================================
# El Auditor: Panel de Control y Diagnóstico Interno
#
# BASE-URL}} indicadores-macro/admin/auditoria?tipo_indicador=LST&fecha_inicio=2026-05-01&fecha_fin=2026-05-05
# ====================================================
@router.get("/admin/auditoria", summary="Auditoría dinámica de registros históricos")
async def auditar_registros_macro(
    entidad_tipo: Optional[str] = Query(None, description="Filtrar por tipo de entidad (ej. municipio)"),
    entidad_id: Optional[str] = Query(None, description="Filtrar por clave (cvegeo o cve_ent)"),
    tipo_indicador: Optional[str] = Query(None, description="Filtrar por indicador (ej. LST, NDVI)"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[date] = Query(None, description="Fecha límite (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint de administración:
    Permite cruzar múltiples filtros para descubrir huecos en los datos 
    y contabilizar el volumen de mapas disponibles por región o indicador.
    """
    registros = await auditar_indicadores(
        db=db,
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        tipo_indicador=tipo_indicador,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )
    
    # Empaquetamos la respuesta agregando un conteo total para facilitar el diagnóstico
    return {
        "status": "success",
        "filtros_aplicados": {
            "entidad_tipo": entidad_tipo,
            "entidad_id": entidad_id,
            "tipo_indicador": tipo_indicador,
            "rango_fechas": f"{fecha_inicio} a {fecha_fin}" if fecha_inicio or fecha_fin else "Todos"
        },
        "total_encontrados": len(registros),
        "data": registros
    }


# ====================================================
# El Cosechador: Ingesta Histórica Masiva
# ====================================================
@router.post("/cosecha-masiva", status_code=status.HTTP_202_ACCEPTED, summary="Desencadenar cosecha histórica")
async def iniciar_cosecha_historica(
    solicitud: CosechaMasivaRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Recibe un rango de fechas, verifica huecos en la base de datos 
    y lanza una ráfaga de descargas en segundo plano hacia Copernicus.
    """
    resultado = await encolar_cosecha_masiva(db, solicitud)
    
    if resultado["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=resultado["message"]
        )
        
    return resultado


# ====================================================
# Webhook Interno (Receptor del Worker en Go)
# ====================================================
@router.post("/webhook/indicador-macro", response_model=IndicadorMacroResponse, status_code=status.HTTP_201_CREATED)
async def webhook_recepcion_cog(
    payload: IndicadorMacroCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook interno: Recibe la confirmación del Worker en Go con la URL del COG.
    Ajustado para soportar operaciones asíncronas con SQLAlchemy 2.0.
    """
    nuevo_indicador = IndicadorMacro(
        id=uuid.uuid4(),
        tipo_indicador=payload.tipo_indicador,
        entidad_tipo=payload.entidad_tipo,
        entidad_id=payload.entidad_id,
        fecha_captura=payload.fecha_captura,
        cog_url=payload.cog_url
    )

    try:
        db.add(nuevo_indicador) # add() no necesita await porque solo prepara el objeto en memoria
        await db.commit()       # ¡Corrección: el commit sí toca la base de datos!
        await db.refresh(nuevo_indicador) # ¡Corrección: el refresh también recarga desde la base!
        return nuevo_indicador
        
    except IntegrityError:
        await db.rollback()     # ¡Corrección: limpiar la sesión fallida!
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El mapa para este indicador, entidad y fecha ya está registrado."
        )
    

# ====================================================
# Endpoint de Series de Tiempo (Para Gráficos en React)
# ====================================================
@router.get("/{entidad_tipo}/{entidad_id}/serie-tiempo", summary="Obtener serie cronológica para gráficos")
async def obtener_serie_tiempo_indicador(
    entidad_tipo: str = Path(..., description="Ej. 'municipio' o 'region'"),
    entidad_id: str = Path(..., description="La clave de la entidad (cvegeo/cve_ent)"),
    tipo_indicador: str = Query(..., description="Ej. 'LST' o 'NDVI'"),
    fecha_inicio: date = Query(..., description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha límite (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Punto de acceso especializado para componentes visuales.
    Siempre retorna un Array (lista). Si no hay datos en el rango, retorna un Array vacío [], 
    evitando que los métodos .map() de React colapsen.
    """
    # Freno de seguridad lógico
    if fecha_inicio > fecha_fin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de inicio no puede ser posterior a la fecha de fin."
        )

    registros = await obtener_serie_tiempo(
        db=db,
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        tipo_indicador=tipo_indicador,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )

    return {
        "status": "success",
        "source": "database",
        "total_registros": len(registros),
        "data": registros
    }


# ====================================================
# Endpoint de Lectura (Frontend React)
# ====================================================
@router.get("/{entidad_tipo}/{entidad_id}", summary="Obtener historial o mapa específico")
async def obtener_indicador(
    entidad_tipo: str = Path(..., description="Ej. 'municipio' o 'region'"),
    entidad_id: str = Path(..., description="La clave de la entidad (cvegeo/cve_ent)"),
    tipo_indicador: str = Query(..., description="Ej. 'LST' o 'NDVI'"),
    fecha_captura: Optional[date] = Query(None, description="Si se omite, devuelve los últimos 5 registros."),
    db: AsyncSession = Depends(get_db)
):
    """
    Punto de acceso de Solo Lectura para React:
    - Si NO hay fecha: Retorna el historial de los últimos 5 mapas.
    - Si HAY fecha: Busca el mapa exacto en la base de datos (Retorna 404 si no existe).
    """
    
    # Escenario A: Búsqueda histórica (El usuario no seleccionó fecha en el calendario)
    if not fecha_captura:
        historial = await obtener_ultimos_registros(
            db=db,
            entidad_id=entidad_id,
            tipo_indicador=tipo_indicador,
            limite=5
        )
        if not historial:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No existen registros de mapas para esta entidad."
            )
        return {"status": "success", "source": "database", "data": historial}

    # Escenario B: Búsqueda por fecha exacta (Estrictamente de lectura)
    registro_existente = await obtener_indicador_por_fecha(
        db=db,
        tipo_indicador=tipo_indicador,
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        fecha_captura=fecha_captura
    )
    
    # Si el dato no está cosechado, bloqueamos cortésmente
    if not registro_existente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Datos no disponibles para {tipo_indicador} en la fecha solicitada. Intente consultar otra fecha disponible en el historial."
        )
    
    return {
        "status": "success", 
        "source": "database", 
        "data": registro_existente
    }

