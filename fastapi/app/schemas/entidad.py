# fastapi/app/schemas/entidad.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any

# ==========================================
# ESQUEMAS BASE
# ==========================================
class EntidadBase(BaseModel):
    cvegeo: str = Field(..., max_length=2)
    cve_ent: str = Field(..., max_length=2)
    nomgeo: str = Field(..., max_length=150)

# ==========================================
# ESQUEMA DE LISTA LIGERA (Para el Select/Buscador del Frontend)
# No incluye la geometría para evitar sobrecargar la red
# ==========================================
class EntidadListResponse(EntidadBase):
    gid: int
    
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# ESQUEMA DE DETALLE (Para dibujar el mapa)
# Incluye la geometría pesada
# ==========================================
class EntidadDetailResponse(EntidadListResponse):
    geom: Dict[str, Any] # Devolveremos el polígono como GeoJSON