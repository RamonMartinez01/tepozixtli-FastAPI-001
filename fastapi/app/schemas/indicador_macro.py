# tepozixtli/fastapi/app/schemas/indicador_macro.py
from pydantic import BaseModel, Field, ConfigDict, HttpUrl
from uuid import UUID
from datetime import date

# NUEVO: El payload estructurado que el Worker de Go enviará a FastAPI
class IndicadorMacroCreate(BaseModel):
    tipo_indicador: str = Field(..., description="Ej. 'LST' o 'NDVI'")
    entidad_tipo: str = Field(..., description="Ej. 'municipio' o 'region'")
    entidad_id: UUID = Field(..., description="ID de la entidad en la base de datos")
    fecha_captura: date = Field(..., description="Fecha de la captura satelital")
    cog_url: str = Field(..., description="URL pública del archivo Cloud Optimized GeoTIFF")

    # Blindaje contra campos extra en el JSON entrante
    model_config = ConfigDict(extra='ignore')

# Esquema de Respuesta: Lo que FastAPI le entregará a React
class IndicadorMacroResponse(BaseModel):
    id: UUID
    tipo_indicador: str
    entidad_tipo: str
    entidad_id: UUID
    fecha_captura: date
    cog_url: str  

    # Permite a Pydantic leer directamente del modelo de SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

# Esquema de Mensajería: Se mantiene intacto para empujar tareas a Redis
class RedisTaskPayload(BaseModel):
    task: str = Field(..., description="Nombre de la tarea, ej. 'fetch_copernicus_data'")
    tipo_indicador: str = Field(..., description="Ej. 'LST' o 'NDVI'")
    entidad_tipo: str = Field(..., description="Ej. 'municipio' o 'region'")
    entidad_id: str = Field(..., description="ID de la entidad (UUID en formato string)")
    fecha_captura: str = Field(..., description="Fecha solicitada en formato YYYY-MM-DD")

class CosechaMasivaRequest(BaseModel):
    entidad_tipo: str = Field(..., description="Ej. 'municipio' o 'region'")
    entidad_id: UUID
    tipo_indicador: str = Field(..., description="Ej. 'LST' o 'NDVI'")
    fecha_inicio: date
    fecha_fin: date