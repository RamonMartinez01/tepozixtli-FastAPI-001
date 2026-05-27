# app/api/router.py
from fastapi import APIRouter
from app.api.routes import region

# Este es el router maestro que agrupará a todos los demás
api_router = APIRouter()

# Aquí conectamos el módulo de regiones. 
# Todas sus rutas heredarán el prefijo '/regiones'
api_router.include_router(region.router, prefix="/regiones", tags=["Regiones Espaciales"])