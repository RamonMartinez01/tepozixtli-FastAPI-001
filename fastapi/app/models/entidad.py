# fastapi/app/models/entidad.py
from sqlalchemy import Column, Integer, String
from geoalchemy2 import Geometry
from app.models.base import Base

class EntidadFederativa(Base):
    __tablename__ = "entidades_federativas"

    # shp2pgsql genera 'gid' como Primary Key
    gid = Column(Integer, primary_key=True, index=True)
    
    # Para los estados, la clave geoestadística y la clave de entidad son idénticas (2 dígitos)
    cvegeo = Column(String(2), index=True, nullable=False)
    cve_ent = Column(String(2), index=True, nullable=False)
    nomgeo = Column(String(150), nullable=False)
    
    # La geometría
    geom = Column(Geometry(geometry_type='MULTIPOLYGON', srid=4326), nullable=False)