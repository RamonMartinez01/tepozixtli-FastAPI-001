# Etapa 1: Construcción del binario
FROM golang:1.24-alpine AS builder

WORKDIR /app

# Copiamos y descargamos dependencias primero para aprovechar la caché de Docker
COPY go.mod go.sum ./
RUN go mod download

# Copiamos el resto del código fuente
COPY . .

# Compilamos el binario de forma estática para Linux
RUN CGO_ENABLED=0 GOOS=linux go build -o satellite-worker main.go

# Etapa 2: Entorno de ejecución limpio
FROM alpine:latest

WORKDIR /app

# Copiamos el binario compilado desde la etapa anterior
COPY --from=builder /app/satellite-worker .

# Ejecutamos el servicio
CMD ["./satellite-worker"]