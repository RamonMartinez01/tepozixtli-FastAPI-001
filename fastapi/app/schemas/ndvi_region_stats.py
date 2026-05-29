from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import date, datetime

# 1. Esquema Base: Las propiedades "core" de una observación satelital
class NdviRegionStatBase(BaseModel):
    fecha_observacion: date = Field(
        ..., 
        description="Fecha en la que el satélite capturó la imagen (NO la fecha de procesamiento)"
    )
    p10: float = Field(..., description="Percentil 10: Límite inferior de salud vegetal (Zona de riesgo)")
    mediana: float = Field(..., description="Mediana (p50): Estado de salud central del terreno")
    p90: float = Field(..., description="Percentil 90: Límite superior (Zona de mayor vigor)")
    
    # El histograma validará que reciba un diccionario JSON válido
    histograma: Dict[str, Any] = Field(
        ..., 
        description="Distribución de frecuencias de píxeles por rango de NDVI"
    )
    
    cobertura_nubes: float = Field(
        0.0, 
        ge=0.0, le=100.0, # Validamos que sea un porcentaje entre 0 y 100
        description="Porcentaje de área oscurecida por nubes"
    )

# 2. Esquema de Creación: El Payload que nuestro Worker en Go enviará mediante POST
class NdviRegionStatCreate(NdviRegionStatBase):
    # Pedimos explícitamente el region_id porque necesitamos saber a qué polígono pertenece
    region_id: UUID = Field(..., description="ID de la región agrícola asociada")

# 3. Esquema de Respuesta: Lo que nuestro backend de Python le servirá al Frontend (React)
class NdviRegionStatResponse(NdviRegionStatBase):
    id: UUID
    region_id: UUID
    created_at: datetime

    # Permite a Pydantic leer directamente desde el modelo de SQLAlchemy 2.0
    model_config = ConfigDict(from_attributes=True)