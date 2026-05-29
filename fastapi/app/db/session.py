# app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# 1. Creamos el motor de la base de datos
# pool_pre_ping=True es un salvavidas: verifica que la conexión siga viva antes de usarla, 
# evitando caídas si la base de datos se reinicia inesperadamente.
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    echo=False,  # Usarlo en True durante el desarrollo permite ver el SQL crudo en la terminal
    pool_pre_ping=True,
)

# 2. Creamos la "fábrica" de sesiones asíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False, # ¡CRÍTICO en asíncrono! Evita que SQLAlchemy borre los datos del objeto de la memoria después de hacer un commit.
)