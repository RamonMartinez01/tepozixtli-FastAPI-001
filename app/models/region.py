# app/models/region.py
import uuid
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from geoalchemy2 import Geometry
from app.models.base import Base

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