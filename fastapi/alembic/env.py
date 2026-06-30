import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 1. Importaciones del Ecosistema
from app.core.config import settings
from app.models.base import Base
from app.models.region import Region
from app.models.ndvi_region_stats import NdviRegionStat
from app.models.municipio import Municipio
from app.models.indicador_macro import IndicadorMacro
from app.models.entidad import EntidadFederativa

# Configuración base de Alembic
config = context.config

# 2. Inyección dinámica de la URL desde las variables de entorno (.env)
config.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URL)

# Configuración de logs
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 3. Enlazamos los metadatos de la clase Base para que Alembic detecte los cambios
target_metadata = Base.metadata

def include_object(object, name, type_, reflected, compare_to):
    """
    Filtro de Alembic: Le dice al autogenerador qué tablas ignorar en la base de datos.
    Protegemos las tablas nativas de PostGIS.
    """
    if type_ == "table" and name == "spatial_ref_sys":
        return False
    return True

def run_migrations_offline() -> None:
    """Ejecuta migraciones en modo 'offline' (sin conectarse a la BD)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        include_object=include_object,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        include_object=include_object,  # <--- Escudo para --op.drop_table('spatial_ref_sys')--
        compare_type=True # <--- Detecta si cambiamos tipos de datos (ej. String(50) a String(100))
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """Configuración del motor asíncrono para Alembic."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    """Punto de entrada de Alembic para migraciones 'online'."""
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()