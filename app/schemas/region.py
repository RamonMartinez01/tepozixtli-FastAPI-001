# app/schemas/region.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, Dict
from uuid import UUID

# 1. Esquema Base: Propiedades que se comparten al crear, leer o actualizar
class RegionBase(BaseModel):
    nombre_region: str = Field(..., max_length=150, description="Nombre único de la región agrícola o de interés")
    descripcion: Optional[str] = Field(None, max_length=255)
    # Aceptamos cualquier diccionario válido para nuestro campo JSONB
    metadatos: Optional[Dict[str, Any]] = None 

# 2. Esquema de Creación: Lo que el Frontend nos debe enviar (El Payload POST)
class RegionCreate(RegionBase):
    # Pedimos la geometría como un diccionario (Típicamente un objeto Geometry de GeoJSON)
    # Ejemplo: {"type": "MultiPolygon", "coordinates": [[[[...]]]]}
    geom: Dict[str, Any] = Field(
        ..., 
        description="Geometría de la región en formato GeoJSON (MultiPolygon)"
    )

# 3. Esquema de Respuesta: Lo que el Backend le devuelve al Frontend
class RegionResponse(RegionBase):
    id: UUID
    geom: Dict[str, Any] # Devolveremos la geometría convertida a GeoJSON para que React la dibuje fácilmente

    # Esto le dice a Pydantic que lea el objeto desde un modelo de SQLAlchemy en lugar de un diccionario estándar.
    model_config = ConfigDict(from_attributes=True)

class RegionUpdate(BaseModel):
    nombre_region: Optional[str] = Field(None, max_length=150)
    descripcion: Optional[str] = Field(None, max_length=255)
    metadatos: Optional[Dict[str, Any]] = None
    geom: Optional[Dict[str, Any]] = None