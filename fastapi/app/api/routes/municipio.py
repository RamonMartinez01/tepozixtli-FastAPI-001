# fastapi/app/api/routes/municipio.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import json

from app.api.deps import get_db
from app.services.municipio_service import municipio_service
from app.schemas.municipio import MunicipioListResponse, MunicipioDetailResponse

router = APIRouter()


# ==============
# carga un archivo de tipo geojson
# POST /api/v1/municipios/upload-geojson
# ==============
@router.post("/upload-geojson", status_code=status.HTTP_201_CREATED)
async def upload_geojson(
    file: UploadFile = File(...), 
    db: AsyncSession = Depends(get_db)
):
    """Recibe un archivo GeoJSON y procesa su ingesta masiva."""
    content = await file.read()
    data = json.loads(content)
    
    # Validamos el esquema contra nuestro contrato Pydantic
    # feature_collection = MunicipioFeatureCollection.model_validate(data)
    
    return await municipio_service.bulk_insert_geojson(db)


# ==============
# Responde una lista de 20 registros, de todos los existentes
# GET /api/v1/municipios/
# ==============
@router.get("/", response_model=List[MunicipioListResponse])
async def list_municipios(
    skip: int = 0, 
    limit: int = 20, 
    db: AsyncSession = Depends(get_db)):
    return await municipio_service.get_multi(db, skip=skip, limit=limit)


# ==============
# Responde una lista todos los existentes 
# que pertenezcan a un CVE_ENT
# GET /api/v1/municipios/{cve_ent}
# ==============
@router.get("/entidad/{cve_ent}", response_model=List[MunicipioListResponse])
async def get_municipios_by_entidad(
    cve_ent: str, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await municipio_service.get_by_entidad(db, cve_ent=cve_ent, skip=skip, limit=limit)


# ==============
# Responde con un único municipio 
# filtrado por cvegeo
# GET /api/v1/municipios/{cvegeo}
# ==============
@router.get("/{cvegeo}", response_model=MunicipioDetailResponse)
async def get_municipio(cvegeo: str, db: AsyncSession = Depends(get_db)):
    municipio = await municipio_service.get_by_cvegeo(db, cvegeo=cvegeo)
    if not municipio:
        raise HTTPException(status_code=404, detail="Municipio no encontrado")
    return municipio