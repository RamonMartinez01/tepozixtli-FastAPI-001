from fastapi import FastAPI

app = FastAPI(
    title="Dashboard Agroespacial - Copernicus API",
    description="Ecosistema Backend para consumo, filtrado y exposición de datos satelitales Sentinel.",
    version="0.1.0",
)

@app.get("/", tags=["Estado Base"])
def root():
    return {
        "status": "online",
        "mensaje": "¡Motores encendidos! La API satelital está operativa y lista para recibir coordenadas."
    }