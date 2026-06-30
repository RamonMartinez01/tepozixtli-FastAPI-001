# fastapi/app/api/routes/entidad.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.deps import get_db
from app.services.entidad_service import entidad_service
from app.schemas.entidad import EntidadListResponse, EntidadDetailResponse

router = APIRouter()

# ==============
# GET /api/v1/entidades/
# ==============
@router.get("/", response_model=List[EntidadListResponse])
async def list_entidades(db: AsyncSession = Depends(get_db)):
    """Devuelve la lista ligera (sin geom) de las entidades federativas."""
    return await entidad_service.get_all(db)

# ==============
# GET /api/v1/entidades/{cve_ent}
# ==============
@router.get("/{cve_ent}", response_model=EntidadDetailResponse)
async def get_entidad(cve_ent: str, db: AsyncSession = Depends(get_db)):
    """Devuelve el registro de una entidad incluyendo su GeoJSON pesado."""
    entidad = await entidad_service.get_by_cve_ent(db, cve_ent=cve_ent)
    if not entidad:
        raise HTTPException(status_code=404, detail="Entidad federativa no encontrada")
    return entidad