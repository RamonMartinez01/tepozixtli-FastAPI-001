# app/db/base.py
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
    Clase base de la que heredarán todos nuestros modelos de base de datos.
    Alembic leerá los metadatos de esta clase para generar las migraciones.
    """
    pass