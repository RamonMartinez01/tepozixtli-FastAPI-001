# app/models/municipio.py
import uuid
from sqlalchemy import String, Float, Boolean, Column
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from app.models.base import Base

class Municipio(Base):
    __tablename__ = "municipios"

    # Identificador interno del sistema
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # === Datos Oficiales (Extraídos del GeoJSON) ===
    
    # CVEGEO: Clave Geoestadística Nacional (ej. "13031"). 
    # Es única por municipio en todo el país, ideal para indexar y evitar duplicados.
    cvegeo: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    
    # CVE_ENT: Clave de la Entidad Federativa (Estado).
    # Le ponemos index=True porque seguramente filtraremos "Todos los municipios de Hidalgo".
    cve_ent: Mapped[str] = mapped_column(String(5), index=True, nullable=False)
    
    # NOMGEO: Nombre de la Entidad Federativa (ej. "Hidalgo")
    nomgeo: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # CVE_MUN: Clave del Municipio (aislada, ej. "031")
    cve_mun: Mapped[str] = mapped_column(String(5), nullable=False)
    
    # NOMMUN: Nombre del municipio (ej. "Jacala de Ledezma")
    # Indexado para búsquedas por nombre en el frontend.
    nommun: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    
    # === Datos Complementarios ===
    # Las coberturas a veces pueden venir vacías en los Shapefiles, 
    # por lo que los marcamos como opcionales (Nullable)
    cov: Mapped[float | None] = mapped_column(Float, nullable=True)
    cov_id: Mapped[float | None] = mapped_column(Float, nullable=True)

    # === Geometría Espacial ===
    # Mantenemos MULTIPOLYGON para soportar territorios fragmentados.
    geom: Mapped[str] = mapped_column(Geometry('MULTIPOLYGON', srid=4326), nullable=False)

    # === Control Interno ===
    is_active: bool = Column(Boolean, default=True, nullable=False)
