from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any
from uuid import UUID
from datetime import date

# 1. Esquema de Respuesta: Lo que FastAPI le entregará a React
class IndicadorMacroResponse(BaseModel):
    id: UUID
    tipo_indicador: str
    entidad_tipo: str
    entidad_id: UUID
    fecha_captura: date
    # Aquí irá el GeoJSON con la cuadrícula de temperaturas
    datos_vectoriales: Dict[str, Any] 

    # Permite a Pydantic leer directamente del modelo de SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

# 2. Esquema de Mensajería: El payload estructurado que empujaremos a Redis para Go
class RedisTaskPayload(BaseModel):
    task: str = Field(..., description="Nombre de la tarea, ej. 'fetch_copernicus_data'")
    tipo_indicador: str = Field(..., description="Ej. 'LST' o 'NDVI'")
    entidad_tipo: str = Field(..., description="Ej. 'municipio' o 'region'")
    entidad_id: str = Field(..., description="ID de la entidad (UUID en formato string)")
    fecha_captura: str = Field(..., description="Fecha solicitada en formato YYYY-MM-DD")