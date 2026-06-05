from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from uuid import UUID

from app.api.deps import get_db 
from app.services.indicador_macro_service import obtener_o_encolar_indicador

router = APIRouter()

# ====================================================
# publicador de Redis en FastAPI para encolar un mensaje con la tarea de extracción si los datos no existen en caché.
# GET /api/v1/indicadores-macro/{entidad_tipo}/{entidad_id}?tipo_indicador=LST&fecha_captura=2026-06-03
# ====================================================
@router.get("/{entidad_tipo}/{entidad_id}", summary="Obtener o procesar indicador macro")
async def obtener_indicador(
    entidad_tipo: str = Path(..., description="El tipo de entidad, ej. 'municipio' o 'region'", example="municipio"),
    entidad_id: UUID = Path(..., description="El UUID del municipio o región"),
    tipo_indicador: str = Query(..., description="El indicador deseado, ej. 'LST'", example="LST"),
    fecha_captura: date = Query(..., description="Fecha de la imagen en formato YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db)
):
    """
    Verifica si el indicador ya existe en la base de datos (Cache-Aside).
    Si no existe, encola la tarea en Redis para que el Worker en Go vaya a Copernicus.
    """
    resultado = await obtener_o_encolar_indicador(
        db=db,
        tipo_indicador=tipo_indicador,
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        fecha_captura=fecha_captura
    )
    
    return resultado