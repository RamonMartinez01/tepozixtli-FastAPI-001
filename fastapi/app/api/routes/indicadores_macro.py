from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from datetime import date
from typing import List, Optional
from uuid import UUID
import uuid

from app.api.deps import get_db 
from app.services.indicador_macro_service import obtener_o_encolar_indicador
from app.models.indicador_macro import IndicadorMacro
from app.schemas.indicador_macro import IndicadorMacroCreate, IndicadorMacroResponse

router = APIRouter()

# ====================================================
# Endpoint Dual: Historial o Búsqueda Específica con Redis
# ====================================================
@router.get("/{entidad_tipo}/{entidad_id}", summary="Obtener historial o procesar indicador macro")
async def obtener_indicador(
    entidad_tipo: str = Path(..., description="Ej. 'municipio' o 'region'"),
    entidad_id: UUID = Path(..., description="El UUID de la entidad"),
    tipo_indicador: str = Query(..., description="Ej. 'LST' o 'NDVI'"),
    fecha_captura: Optional[date] = Query(None, description="Si se omite, devuelve los últimos 5 registros."),
    db: AsyncSession = Depends(get_db)
):
    """
    Punto de acceso para React:
    - Si NO hay fecha: Retorna el historial de los últimos 5 mapas.
    - Si HAY fecha: Busca el mapa exacto o encola la tarea a Go si no existe.
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
        # Retornamos la lista bajo la misma estructura para que React no se confunda
        return {"status": "success", "source": "database", "data": historial}

    # Escenario B: Búsqueda por fecha exacta (Con activación del Worker si hay fallo)
    resultado = await obtener_o_encolar_indicador(
        db=db,
        tipo_indicador=tipo_indicador,
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        fecha_captura=fecha_captura
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