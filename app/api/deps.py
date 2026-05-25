# app/api/deps.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Generador de sesiones asíncronas para la base de datos.
    Se inyectará en los endpoints de FastAPI.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            # El bloque finally asegura que la conexión regrese al pool
            # sin importar si la petición fue exitosa o si explotó por un error.
            await session.close()