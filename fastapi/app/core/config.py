# app/core/config.py
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Obtenemos la ruta absoluta de la carpeta raíz del proyecto (/tepozixtli)
# Si config.py está en /fastapi/app/core/, subimos 3 niveles para llegar a la raíz.
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    PROJECT_NAME: str = "Dashboard Agroespacial - Copernicus"

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    
    # Base de Datos
    SQLALCHEMY_DATABASE_URL: str
    
    # Frontend
    FRONTEND_URL: str = "FRONTEND_URL"
    
    # Seguridad y JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Token Interno para microservicios
    INTERNAL_API_TOKEN: str 
    
    # Configuración de Pydantic para que lea automáticamente el archivo .env
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH), 
        env_file_encoding="utf-8")

settings = Settings()