FROM python:3.12-slim

# Actualizar los paquetes del sistema operativo base para parchar vulnerabilidades.
RUN apt-get update && \
    apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*

# Evita que Python escriba archivos .pyc en el disco (ahorra espacio)
ENV PYTHONDONTWRITEBYTECODE=1
# Evita que Python almacene en búfer la salida estándar (para ver los logs en tiempo real)
ENV PYTHONUNBUFFERED=1

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalamos dependencias del sistema necesarias para compilar algunas librerías de Python (como asyncpg)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiamos solo el archivo de requerimientos primero (para aprovechar la caché de Docker)
COPY requirements.txt .

# Instalamos las librerías de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el código de nuestra aplicación al contenedor
COPY . .

# Exponemos el puerto donde vivirá FastAPI
EXPOSE 8000

# El comando de ignición para encender el servidor (usando el host 0.0.0.0 para que sea accesible)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--forwarded-allow-ips", "*"]