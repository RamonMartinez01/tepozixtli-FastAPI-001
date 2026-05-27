# app/models/region.py
import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Column, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from geoalchemy2 import Geometry
from app.models.base import Base

# --- Truco para Evitar Importación Circular ---
# Esto solo se ejecuta para el linter de VSCode, no en tiempo de ejecución.
if TYPE_CHECKING:
    from app.models.ndvi_region_stats import NdviRegionStat

class Region(Base):
    __tablename__ = "regiones"

    # Estilo SQLAlchemy 2.0
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_region: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    descripcion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
  
    # Usamos MULTIPOLYGON para soportar regiones geográficas desconectadas (ej. con islas o fragmentadas)
    # comunes al importar archivos SHP o GeoJSON.
    geom: Mapped[str] = mapped_column(Geometry('MULTIPOLYGON', srid=4326), nullable=False)

    # sin ningún propósito concreto todabía
    metadatos: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    is_active: bool = Column(Boolean, default=True, nullable=False)

    # === NUEVA RELACIÓN AL ESTILO 2.0 ===
    # Indicamos que una región puede tener múltiples estadísticas (una lista)
    ndvi_stats: Mapped[List["NdviRegionStat"]] = relationship(
        "NdviRegionStat", 
        back_populates="region", 
        cascade="all, delete-orphan"
    )