# fastapi/app/models/indicador_macro.py
import uuid
from datetime import date
from sqlalchemy import String, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base

class IndicadorMacro(Base):
    __tablename__ = "indicadores_macro"

    # ID único del registro
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Qué indicador es (Ej. "LST", "NDVI")
    tipo_indicador: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Si pertenece a un municipio o región (Ej. "municipio")
    entidad_tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Ahora es STRING para alojar el cvegeo (5) o cve_ent (2)
    entidad_id: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    
    # De cuándo es la imagen del satélite
    fecha_captura: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    
    # El tesoro: La ubicación exacta del mapa optimizado en la nube
    cog_url: Mapped[str] = mapped_column(String(500), nullable=False)

    # Restricción: No podemos tener el mismo indicador, para la misma entidad, en la misma fecha
    __table_args__ = (
        UniqueConstraint(
            'tipo_indicador', 'entidad_tipo', 'entidad_id', 'fecha_captura', 
            name='uix_indicador_entidad_fecha'
        ),
    )