import os
import uuid 
from typing import List 
from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.ndvi_region_stats import NdviRegionStatCreate, NdviRegionStatResponse
from app.services.ndvi_region_stats_service import ndvi_stats_service
from app.core.config import settings

router = APIRouter()

# ==========================================
#  ESCUDO DE SEGURIDAD INTERNO
# ==========================================


# FastAPI buscará automáticamente este Header en la petición
api_key_header = APIKeyHeader(name="X-Internal-Token", auto_error=True)

async def verify_internal_token(api_key_header: str = Security(api_key_header)):
    if api_key_header != settings.INTERNAL_API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: Token interno inválido. Solo el Ingestor autorizado puede atracar aquí."
        )
    return api_key_header


# ==========================================
#  ENDPOINTS
# ==========================================

# ==========================================
# POST
# /api/v1/internal/region-ndvi-stats/
# ==========================================
@router.post("/internal/region-ndvi-stats/", response_model=NdviRegionStatResponse, status_code=status.HTTP_201_CREATED)
async def inyectar_estadisticas_ndvi(
    stat_in: NdviRegionStatCreate,
    db: AsyncSession = Depends(get_db),
    # Al inyectar el token como dependencia, blindamos la ruta
    token: str = Depends(verify_internal_token) 
):
    """
    Recibe las estadísticas de NDVI procesadas por el worker satelital en Go.
    Realiza un 'Upsert' (Actualiza si existe, crea si no existe) para garantizar idempotencia.
    """
    try:
        nueva_estadistica = await ndvi_stats_service.create_or_update(db=db, stat_in=stat_in)
        return nueva_estadistica
    except Exception as e:
        # Interceptamos errores de base de datos para no exponer la traza completa
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error en el motor de persistencia: {str(e)}"
        )
    
# ==========================================
# GET: CONSUMO PARA EL FRONTEND (Público/Sin Token Interno)
# /api/v1/regiones/{region_id}/ndvi-stats/
# ==========================================
@router.get("/regiones/{region_id}/ndvi-stats/", response_model=List[NdviRegionStatResponse])
async def obtener_historial_ndvi(
    region_id: uuid.UUID,
    limit: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene la serie temporal de NDVI para una región específica.
    Este endpoint NO requiere el token interno, ya que será consumido por el frontend en React
    para dibujar las gráficas históricas.
    """
    historial = await ndvi_stats_service.get_history_by_region(db=db, region_id=region_id, limit=limit)
    return historial


# ==========================================
# DELETE: OPERABILIDAD INTERNA (Protegido por Token)
# /api/v1/internal/region-ndvi-stats/{stat_id}
# ==========================================
@router.delete("/internal/region-ndvi-stats/{stat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_estadistica_ndvi(
    stat_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(verify_internal_token) # <-- Nuestro escudo protector
):
    """
    Elimina un registro específico de NDVI. 
    Exclusivo para operabilidad interna (limpiar mocks, corregir errores).
    """
    eliminado = await ndvi_stats_service.delete_stat(db=db, stat_id=stat_id)
    if not eliminado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La estadística satelital no existe o ya fue eliminada."
        )
    
    return