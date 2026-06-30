# fastapi/app/models/municipio.py
from sqlalchemy import Column, Integer, String
from geoalchemy2 import Geometry
from app.models.base import Base

class Municipio(Base):
    __tablename__ = "municipios"

    # shp2pgsql siempre crea un 'gid' autoincremental como Primary Key
    gid = Column(Integer, primary_key=True, index=True)
    cvegeo = Column(String(10), index=True, nullable=False)
    cve_ent = Column(String(5), index=True, nullable=False)
    cve_mun = Column(String(5), index=True, nullable=False)
    nomgeo = Column(String(150), nullable=False)
    
    # La geometría
    geom = Column(Geometry(geometry_type='MULTIPOLYGON', srid=4326), nullable=False)