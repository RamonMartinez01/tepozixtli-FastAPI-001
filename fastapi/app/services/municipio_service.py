# fastapi/app/api/routes/municipio_service.py
import json
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from app.models.municipio import Municipio
from app.schemas.municipio import MunicipioBase, MunicipioListResponse

class MunicipioService:
   
    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 20) -> List[dict]:
        """
        Obtiene una lista paginada de municipios SIN su Geometría.
        """
        stmt = select(
            Municipio.gid,
            Municipio.cvegeo,
            Municipio.cve_ent,
            Municipio.cve_mun,
            Municipio.nomgeo,
            ).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return [row._asdict() for row in result.all()]

    @staticmethod
    async def get_by_entidad(db: AsyncSession, cve_ent: str, skip: int = 0, limit: int = 100) -> List[dict]:
        """
        Filtra y devuelve todos los municipios de una entidad federativa,
        SIN su Geometría.
        """
        stmt = select(
            Municipio.gid,
            Municipio.cvegeo,
            Municipio.cve_ent,
            Municipio.cve_mun,
            Municipio.nomgeo,
            ).where(Municipio.cve_ent == cve_ent).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return [row._asdict() for row in result.all()]

    @staticmethod
    async def get_by_cvegeo(db: AsyncSession, cvegeo: str) -> Optional[dict]:
        """Busca un municipio y decodifica su geometría con ST_AsGeoJSON."""
        stmt = select(
            Municipio.gid,
            Municipio.cvegeo,
            Municipio.cve_ent,
            Municipio.cve_mun,
            Municipio.nomgeo,
            func.ST_AsGeoJSON(Municipio.geom).label("geom_json")
        ).where(Municipio.cvegeo == cvegeo)
        
        result = await db.execute(stmt)
        row = result.fetchone()
        
        if not row:
            return None
            
        municipio_dict = row._asdict()
        municipio_dict["geom"] = json.loads(municipio_dict["geom_json"])
        return municipio_dict
    
# Instancia única para ser importada en los controladores
municipio_service = MunicipioService()