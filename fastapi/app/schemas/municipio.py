# fastapi/app/schemas/municipio.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from uuid import UUID

# ==========================================
# 1. ESQUEMAS BASE Y DE RESPUESTA (Salida)
# ==========================================
class MunicipioBase(BaseModel):
    cvegeo: str = Field(..., max_length=10)
    cve_ent: str = Field(..., max_length=5)
    nomgeo: str = Field(..., max_length=100)
    cve_mun: str = Field(..., max_length=5)
    nommun: str = Field(..., max_length=150)
    cov: Optional[float] = None
    cov_id: Optional[float] = None

class MunicipioResponse(MunicipioBase):
    id: UUID
    geom: Dict[str, Any] # Devolveremos la geometría como GeoJSON al frontend

    model_config = ConfigDict(from_attributes=True)

# 3. ESQUEMA DE CREACIÓN INDIVIDUAL (Desde formulario UI)
class MunicipioCreate(MunicipioBase):
    """
    Payload esperado cuando el Frontend envía un solo municipio 
    a través de un formulario.
    """
    geom: Dict[str, Any] = Field(
        ..., 
        description="Geometría del municipio en formato GeoJSON (MultiPolygon)"
    )

# ==========================================
# 2. ESQUEMAS DE INGESTA (Entrada del GeoJSON)
# ==========================================
# Este esquema valida el diccionario "properties" de cada municipio en tu archivo
class MunicipioProperties(BaseModel):
    CVEGEO: str
    CVE_ENT: str
    NOMGEO: str
    CVE_MUN: str
    NOMMUN: str
    cov_: Optional[float] = None  # Nota: Atrapamos "cov_" tal como viene en tu archivo
    cov_id: Optional[float] = None

# Este esquema valida la estructura de un "Feature" individual
class MunicipioFeature(BaseModel):
    type: str
    properties: MunicipioProperties
    geometry: Dict[str, Any] # Aquí viene el MultiPolygon

# Este es el contrato final que validará todo el archivo subido
class MunicipioFeatureCollection(BaseModel):
    type: str
    features: List[MunicipioFeature]
