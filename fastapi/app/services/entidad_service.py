# fastapi/app/services/entidad_service.py
import json
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.entidad import EntidadFederativa

class EntidadService:
    
    @staticmethod
    async def get_all(db: AsyncSession) -> List[dict]:
        """
        Obtiene el catálogo de las 32 entidades sin la geometría.
        Ideal para poblar el selector principal del Frontend al instante.
        """
        stmt = select(
            EntidadFederativa.gid,
            EntidadFederativa.cvegeo,
            EntidadFederativa.cve_ent,
            EntidadFederativa.nomgeo
        ).order_by(EntidadFederativa.nomgeo) # Las ordenamos alfabéticamente
        
        result = await db.execute(stmt)
        rows = result.all()
        
        # Como no hay geometría que parsear, la conversión es directa
        return [row._asdict() for row in rows]

    @staticmethod
    async def get_by_cve_ent(db: AsyncSession, cve_ent: str) -> Optional[dict]:
        """
        Obtiene el detalle de una entidad, decodificando su polígono GeoJSON.
        """
        stmt = select(
            EntidadFederativa.gid,
            EntidadFederativa.cvegeo,
            EntidadFederativa.cve_ent,
            EntidadFederativa.nomgeo,
            func.ST_AsGeoJSON(EntidadFederativa.geom).label("geom_json")
        ).where(EntidadFederativa.cve_ent == cve_ent)
        
        result = await db.execute(stmt)
        row = result.fetchone()
        
        if not row:
            return None
            
        entidad_dict = row._asdict()
        entidad_dict["geom"] = json.loads(entidad_dict["geom_json"])
        return entidad_dict

# Instancia única
entidad_service = EntidadService()