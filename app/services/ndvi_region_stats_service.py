from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import uuid
import datetime

from app.models.ndvi_region_stats import NdviRegionStat
from app.schemas.ndvi_region_stats import NdviRegionStatCreate

class NdviRegionStatsService:
    
    async def create_or_update(self, db: AsyncSession, stat_in: NdviRegionStatCreate) -> NdviRegionStat:
        """
        Recibe un payload del worker satelital. 
        Si ya existe una medición para esa región en esa fecha, la actualiza. 
        Si no existe, crea un nuevo registro.
        """
        # 1. Buscamos si ya hay un registro para este ID de región en esta fecha exacta
        stmt = select(NdviRegionStat).where(
            NdviRegionStat.region_id == stat_in.region_id,
            NdviRegionStat.fecha_observacion == stat_in.fecha_observacion
        )
        result = await db.execute(stmt)
        db_stat = result.scalar_one_or_none()

        if db_stat:
            # 2a. Si existe, actualizamos sus valores (Upsert)
            # Esto nos protege de datos duplicados si el worker de Go reintenta una petición
            update_data = stat_in.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_stat, field, value)
        else:
            # 2b. Si no existe, creamos la nueva instancia
            db_stat = NdviRegionStat(**stat_in.model_dump())
            db.add(db_stat)

        # 3. Guardamos los cambios en la base de datos
        await db.commit()
        await db.refresh(db_stat)
        
        return db_stat

    async def get_history_by_region(
        self, db: AsyncSession, region_id: uuid.UUID, limit: int = 30
    ) -> list[NdviRegionStat]:
        """
        Método extra (bonus) para el futuro: 
        Obtiene la serie temporal de una región, ordenada por fecha (las más recientes primero).
        """
        stmt = select(NdviRegionStat).where(
            NdviRegionStat.region_id == region_id
        ).order_by(NdviRegionStat.fecha_observacion.desc()).limit(limit)
        
        result = await db.execute(stmt)
        return list(result.scalars().all())
    

    async def delete_stat(self, db: AsyncSession, stat_id: uuid.UUID) -> bool:
        """
        Elimina físicamente un registro de estadística por su ID.
        Útil para limpiar datos de prueba (mocks) o revertir ingestas erróneas.
        """
        stmt = select(NdviRegionStat).where(NdviRegionStat.id == stat_id)
        result = await db.execute(stmt)
        db_stat = result.scalar_one_or_none()
        
        if db_stat:
            await db.delete(db_stat)
            await db.commit()
            return True
            
        return False

# Instanciamos el Singleton para importarlo limpiamente en las rutas
ndvi_stats_service = NdviRegionStatsService()