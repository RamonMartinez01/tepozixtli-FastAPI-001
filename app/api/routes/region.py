# app/api/routes/region.py
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from app.api.deps import get_db
from app.schemas.region import RegionCreate, RegionResponse, RegionUpdate
from app.services.region_service import region_service

router = APIRouter()

# ==============
# 
# POST /api/v1/regions/
# ==============
@router.post("/", response_model=RegionResponse, status_code=status.HTTP_201_CREATED)
async def crear_region(region_in: RegionCreate, db: AsyncSession = Depends(get_db)):
    """
    Registra una nueva región agrícola con sus coordenadas espaciales GeoJSON.
    """
    try:
        nueva_region = await region_service.create(db=db, region_in=region_in)
        return nueva_region
    except Exception as e:
        # Si ocurre una colisión (como un nombre duplicado) o un GeoJSON inválido, 
        # interceptamos el error y devolvemos un 400 Bad Request en lugar de un 500.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al registrar la región: {str(e)}"
        )
    

# ==============
# 
# GET/api/v1/regions/{region_id}
# ==============
@router.get("/{region_id}", response_model=RegionResponse)
async def obtener_region_por_id(
    region_id: UUID, 
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene una región específica por su UUID.
    Si la región no existe, devuelve un error 404.
    """
    region = await region_service.get_by_id(db=db, region_id=region_id)
    
    if not region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró ninguna región con el ID: {region_id}"
        )
        
    return region
    

# ==============
# 
# GET/api/v1/regions/{region_id}
# ==============
@router.get("/", response_model=List[RegionResponse])
async def listar_regiones(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """
    Obtiene el catálogo de regiones registradas, listas para ser dibujadas en el mapa.
    """
    regiones = await region_service.get_all(db=db, skip=skip, limit=limit)
    return regiones


# ==============
# 
# PATCH /api/v1/regions/{region_id}
# ==============
@router.patch("/{region_id}", response_model=RegionResponse)
async def actualizar_region(
    region_id: UUID, 
    region_in: RegionUpdate = Body(...), 
    db: AsyncSession = Depends(get_db)):
    updated = await region_service.update(db=db, region_id=region_id, data=region_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Región no encontrada")
    return updated


# ==============
# 
# DELETE /api/v1/regions/{region_id}
# ==============
@router.delete("/{region_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_region(
    region_id: UUID, 
    db: AsyncSession = Depends(get_db)):
    success = await region_service.soft_delete(db=db, region_id=region_id)
    if not success:
        raise HTTPException(status_code=404, detail="Región no encontrada")
    return None