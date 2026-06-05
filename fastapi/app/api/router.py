# app/api/router.py
from fastapi import APIRouter
from app.api.routes import region
from app.api.routes import ndvi_region_stats
from app.api.routes import municipio
from app.test_redis_route import router as test_router

# Este es el router maestro que agrupará a todos los demás
api_router = APIRouter()

# Aquí conectamos el módulo de regiones. 
# Todas sus rutas heredarán el prefijo '/regiones'
api_router.include_router(region.router, prefix="/regiones", tags=["Regiones Espaciales"])

# Nota: el prefijo ya lo incluimos en la definición de la ruta, 
# pero puedes ajustarlo según la convención de tu proyecto).
api_router.include_router(ndvi_region_stats.router, tags=["Internal Microservices"])

api_router.include_router(municipio.router, prefix="/municipios", tags=["Municipios"])

# test de redis
api_router.include_router(test_router)