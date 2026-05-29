# app/services/region_service.py
import json
from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from shapely.geometry import shape, mapping
from shapely import wkb

from app.models.region import Region
from app.schemas.region import RegionCreate, RegionUpdate

class RegionService:
    
    async def create(self, db: AsyncSession, region_in: RegionCreate) -> Region:
        
        """
        Recibe un payload validado, transforma el GeoJSON a formato PostGIS, 
        y lo inserta asíncronamente en la base de datos.
        """
        # 1. Transformación de Entrada (Frontend -> Base de Datos)
        # Convertimos el diccionario GeoJSON en un objeto geométrico de Shapely
        geom_shape = shape(region_in.geom)
        # Ensamblamos el formato WKT
        wkt_geom = f"SRID=4326;{geom_shape.wkt}"

        # 2. Transacción de Base de Datos
        db_region = Region(
            nombre_region=region_in.nombre_region,
            descripcion=region_in.descripcion,
            metadatos=region_in.metadatos,
            geom=wkt_geom
        )
        
        db.add(db_region)
        await db.commit()
        await db.refresh(db_region)
        
        # 3. LA CLAVE: No usamos to_shape. 
        # Volvemos a consultar la base de datos pidiendo explícitamente el GeoJSON
        # para asegurar que tenemos la representación correcta.
        stmt = select(func.ST_AsGeoJSON(Region.geom)).where(Region.id == db_region.id)
        result = await db.execute(stmt)
        geo_json_str = result.scalar()

        # 4. Convertimos el JSON string a dict para la respuesta
        import json
        db_region.geom = json.loads(geo_json_str)
        
        return db_region
        

    async def get_by_id(self, db: AsyncSession, region_id: UUID) -> Optional[Region]:
        """Busca una región por su UUID y decodifica su geometría."""
        query = select(Region).where(Region.id == region_id)
        result = await db.execute(query)
        region = result.scalar_one_or_none()
        
        if region and region.geom:
            # Desempaquetar WKB a GeoJSON
            region.geom = mapping(wkb.loads(str(region.geom.data), hex=True))
            
        return region
    
    async def get_by_id(self, db: AsyncSession, region_id: UUID) -> Optional[dict]:
        """Busca una región y devuelve los datos con la geometría ya convertida."""
        stmt = select(
            Region.id,
            Region.nombre_region,
            Region.descripcion,
            Region.metadatos,
            func.ST_AsGeoJSON(Region.geom).label("geom_json")
        ).where(Region.id == region_id, Region.is_active == True)
        
        result = await db.execute(stmt)
        row = result.fetchone()
        
        if not row:
            return None
            
        # Convertimos a diccionario incluyendo la geometría procesada
        region_dict = row._asdict()
        region_dict["geom"] = json.loads(region_dict["geom_json"])
        return region_dict

    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[dict]:
        """Obtiene lista paginada con geometrías listas para el frontend."""
        stmt = select(
            Region.id,
            Region.nombre_region,
            Region.descripcion,
            Region.metadatos,
            func.ST_AsGeoJSON(Region.geom).label("geom_json")
        ).where(Region.is_active == True).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        rows = result.all()
        
        regiones = []
        for row in rows:
            data = row._asdict()
            data["geom"] = json.loads(data["geom_json"])
            regiones.append(data)
            
        return regiones
    
    async def update(self, db: AsyncSession, region_id: UUID, data: RegionUpdate) -> Optional[Region]:
        update_data = data.model_dump(exclude_unset=True)
        
        # Si vienen datos geométricos, los convertimos a WKT
        if "geom" in update_data:
            geom_shape = shape(update_data["geom"])
            update_data["geom"] = f"SRID=4326;{geom_shape.wkt}"
        
        stmt = update(Region).where(Region.id == region_id).values(**update_data).returning(Region)
        result = await db.execute(stmt)
        await db.commit()
        
        updated_region = result.scalar_one_or_none()
        if updated_region:
            # Re-convertimos la geometría a GeoJSON para la respuesta
            geo_json_str = await db.scalar(select(func.ST_AsGeoJSON(Region.geom)).where(Region.id == region_id))
            updated_region.geom = json.loads(geo_json_str)
            
        return updated_region
    

    async def soft_delete(self, db: AsyncSession, region_id: UUID) -> bool:
        stmt = update(Region).where(Region.id == region_id).values(is_active=False)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

# Instanciamos el servicio para usarlo directamente como un Singleton en nuestras rutas
region_service = RegionService()