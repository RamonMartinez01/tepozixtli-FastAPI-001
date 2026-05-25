# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Dashboard Agroespacial - Copernicus"
    
    # Base de Datos
    SQLALCHEMY_DATABASE_URL: str
    
    # Frontend
    FRONTEND_URL: str = "FRONTEND_URL"
    
    # Seguridad y JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Configuración de Pydantic para que lea automáticamente el archivo .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()