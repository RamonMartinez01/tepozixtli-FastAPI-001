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
    nomgeo: str = Field(..., max_length=150)
    cve_mun: str = Field(..., max_length=5)
    # cov: Optional[float] = None
    # cov_id: Optional[float] = None

class MunicipioListResponse(MunicipioBase):
    gid: int
    
    model_config = ConfigDict(from_attributes=True)


class MunicipioDetailResponse(MunicipioListResponse):
    geom: Dict[str, Any]

