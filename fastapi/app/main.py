# tepozixtli/fastapi/app/main.py
from fastapi import FastAPI
from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router

app = FastAPI(
    title="Dashboard Agroespacial - Copernicus API",
    description="Ecosistema Backend para consumo, filtrado y exposición de datos satelitales Sentinel.",
    version="0.1.0",
)

# ============================================================
# CORS
# ============================================================
origins = [
    settings.FRONTEND_URL
]

# 3. Añadimos el middleware a la aplicación
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # Permite a estos orígenes comunicarse
    allow_credentials=True,           # Permite el envío de cookies/credenciales
    allow_methods=["*"],              # Permite todos los métodos (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],              # Permite todos los headers
)

# Conectamos todo el panel de enrutamiento bajo el prefijo /api/v1
app.include_router(api_router, prefix="/api/v1")


# Check
@app.get("/", tags=["Estado Base"])
def root():
    return {
        "status": "online",
        "mensaje": "¡Motores encendidos!."
    }