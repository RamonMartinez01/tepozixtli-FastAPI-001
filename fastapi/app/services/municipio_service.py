# fastapi/app/api/routes/municipio_service.py
import json
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from app.models.municipio import Municipio
from app.schemas.municipio import MunicipioCreate, MunicipioFeatureCollection

class MunicipioService:
    
    @staticmethod
    async def create(db: AsyncSession, municipio_in: MunicipioCreate) -> Municipio:
        """
        Crea un único municipio (Ideal para peticiones UI/Formularios).
        """
        # Convertimos el diccionario de la geometría a un string JSON
        geom_json_str = json.dumps(municipio_in.geom)
        
        nuevo_municipio = Municipio(
            cvegeo=municipio_in.cvegeo,
            cve_ent=municipio_in.cve_ent,
            nomgeo=municipio_in.nomgeo,
            cve_mun=municipio_in.cve_mun,
            nommun=municipio_in.nommun,
            cov=municipio_in.cov,
            cov_id=municipio_in.cov_id,
            geom=func.ST_GeomFromGeoJSON(geom_json_str)
        )
        
        db.add(nuevo_municipio)
        await db.commit()
        await db.refresh(nuevo_municipio)
        
        # --- LA CLAVE (Idéntico a region_service) ---
        # Volvemos a consultar la base de datos pidiendo explícitamente el GeoJSON
        # para asegurar que tenemos la representación correcta.
        stmt = select(func.ST_AsGeoJSON(Municipio.geom)).where(Municipio.id == nuevo_municipio.id)
        result = await db.execute(stmt)
        geo_json_str = result.scalar()

        # Reemplazamos el WKBElement (binario) por el diccionario que espera Pydantic
        nuevo_municipio.geom = json.loads(geo_json_str)
        
        return nuevo_municipio

    @staticmethod
    async def bulk_insert_geojson(db: AsyncSession, feature_collection: MunicipioFeatureCollection) -> dict:
        """
        Procesa y guarda un archivo completo de GeoJSON con múltiples municipios.
        """
        nuevos_municipios = []
        
        # Iteramos sobre el contrato validado por Pydantic
        for feature in feature_collection.features:
            geom_json_str = json.dumps(feature.geometry)
            props = feature.properties
            
            municipio = Municipio(
                cvegeo=props.CVEGEO,
                cve_ent=props.CVE_ENT,
                nomgeo=props.NOMGEO,
                cve_mun=props.CVE_MUN,
                nommun=props.NOMMUN,
                cov=props.cov_,     # El mapeo perfecto de tu archivo a nuestro modelo
                cov_id=props.cov_id,
                geom=func.ST_GeomFromGeoJSON(geom_json_str)
            )
            nuevos_municipios.append(municipio)
        
        # add_all es el estándar de oro para inserciones masivas en SQLAlchemy
        db.add_all(nuevos_municipios)
        await db.commit()
        
        return {
            "mensaje": "Ingesta masiva completada con éxito.",
            "total_insertados": len(nuevos_municipios)
        }

    @staticmethod
    async def get_multi(db: AsyncSession, skip: int = 0, limit: int = 20) -> List[dict]:
        """
        Obtiene una lista paginada de municipios con su geometría decodificada.
        Coherente con la arquitectura de RegionService.get_all.
        """
        stmt = select(
            Municipio.id,
            Municipio.cvegeo,
            Municipio.cve_ent,
            Municipio.nomgeo,
            Municipio.cve_mun,
            Municipio.nommun,
            Municipio.cov,
            Municipio.cov_id,
            func.ST_AsGeoJSON(Municipio.geom).label("geom_json")
        ).where(Municipio.is_active == True).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        rows = result.all()
        
        municipios = []
        for row in rows:
            data = row._asdict()
            # Traducimos el string GeoJSON de PostGIS a un dict de Python
            data["geom"] = json.loads(data["geom_json"])
            municipios.append(data)
            
        return municipios

    @staticmethod
    async def get_by_entidad(db: AsyncSession, cve_ent: str) -> List[dict]:
        """
        Filtra y devuelve todos los municipios de una entidad federativa,
        decodificando las geometrías en el proceso.
        """
        stmt = select(
            Municipio.id,
            Municipio.cvegeo,
            Municipio.cve_ent,
            Municipio.nomgeo,
            Municipio.cve_mun,
            Municipio.nommun,
            Municipio.cov,
            Municipio.cov_id,
            func.ST_AsGeoJSON(Municipio.geom).label("geom_json")
        ).where(Municipio.cve_ent == cve_ent, Municipio.is_active == True)
        
        result = await db.execute(stmt)
        rows = result.all()
        
        municipios = []
        for row in rows:
            data = row._asdict()
            # Traducimos el string GeoJSON de PostGIS a un dict de Python
            data["geom"] = json.loads(data["geom_json"])
            municipios.append(data)
            
        return municipios

    @staticmethod
    async def get_by_cvegeo(db: AsyncSession, cvegeo: str) -> Optional[dict]:
        """Busca un municipio y decodifica su geometría con ST_AsGeoJSON."""
        stmt = select(
            Municipio.id,
            Municipio.cvegeo,
            Municipio.cve_ent,
            Municipio.nomgeo,
            Municipio.cve_mun,
            Municipio.nommun,
            Municipio.cov,
            Municipio.cov_id,
            func.ST_AsGeoJSON(Municipio.geom).label("geom_json")
        ).where(Municipio.cvegeo == cvegeo, Municipio.is_active == True)
        
        result = await db.execute(stmt)
        row = result.fetchone()
        
        if not row:
            return None
            
        municipio_dict = row._asdict()
        municipio_dict["geom"] = json.loads(municipio_dict["geom_json"])
        return municipio_dict
    
# Instancia única para ser importada en los controladores
municipio_service = MunicipioService()