import os
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