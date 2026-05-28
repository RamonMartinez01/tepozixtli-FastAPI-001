import uuid
import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import Float, Date, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base 

# --- Truco para Evitar Importación Circular ---
# Esto solo se ejecuta para el linter de VSCode, no en tiempo de ejecución.
if TYPE_CHECKING:
    from app.models.region import Region

class NdviRegionStat(Base):
    __tablename__ = "ndvi_region_stats"

    # 1. Identificadores
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    region_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("regiones.id", ondelete="CASCADE"), nullable=False, index=True)

    # 2. Dimensión Temporal
    fecha_observacion: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)

    # 3. Métricas de Distribución (El Semáforo Agrícola)
    p10: Mapped[float] = mapped_column(Float, nullable=False)
    mediana: Mapped[float] = mapped_column(Float, nullable=False)
    p90: Mapped[float] = mapped_column(Float, nullable=False)

    # 4. Histograma de Frecuencias
    # Usamos dict[str, Any] para decirle a Python/Mypy que esto es un diccionario.
    histograma: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # 5. Calidad del Dato
    cobertura_nubes: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # 6. Auditoría Interna
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relación bidireccional (Notar las comillas para evaluación perezosa / lazy evaluation)
    region: Mapped["Region"] = relationship("Region", back_populates="ndvi_stats")