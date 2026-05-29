# app/main.py
from fastapi import FastAPI
from app.api.router import api_router

app = FastAPI(
    title="Dashboard Agroespacial - Copernicus API",
    description="Ecosistema Backend para consumo, filtrado y exposición de datos satelitales Sentinel.",
    version="0.1.0",
)

# Conectamos todo el panel de enrutamiento bajo el prefijo /api/v1
app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["Estado Base"])
def root():
    return {
        "status": "online",
        "mensaje": "¡Motores encendidos!."
    }