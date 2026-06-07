# --- FASE DE CONSTRUCCIÓN ---
FROM golang:latest AS builder

# Instalamos las dependencias del sistema necesarias para GDAL y CGO
RUN apt-get update && apt-get install -y --no-install-recommends\
    libgdal-dev \
    gdal-bin \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Definimos que usaremos CGO para compilar los bindings de GDAL
ENV CGO_ENABLED=1

WORKDIR /app

# Copiamos primero los archivos de dependencias para aprovechar el caché de Docker
COPY go.mod go.sum ./
RUN go mod download

# Copiamos el resto del código
COPY . .

# Compilamos el binario
RUN go build -o worker ./cmd/worker/main.go

# --- FASE DE EJECUCIÓN (Imagen final ligera) ---
FROM debian:bullseye-slim

# Ajuste: Instalamos gdal-bin en lugar de una versión fija.
# Esto trae las librerías necesarias automáticamente y es más estable.
# Usamos --fix-missing por si hay algún problema de red con el espejo de Debian.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /root/
COPY --from=builder /app/worker .

CMD ["./worker"]