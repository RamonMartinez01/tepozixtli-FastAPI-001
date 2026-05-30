// tepozixtli/worker/config/env.go
package config

import (
	"log"
	"os"

	"github.com/joho/godotenv"
)

// AppConfig almacena las variables de entorno de nuestra aplicación
type AppConfig struct {
	InternalAPIToken       string
	CopernicusClientID     string
	CopernicusClientSecret string
	WorkerMode             string
}

// LoadConfig lee el archivo .env y mapea las variables a la estructura AppConfig
func LoadConfig() *AppConfig {
	// Subimos un nivel desde /worker para leer el .env en la raíz
	err := godotenv.Load("../.env")
	if err != nil {
		log.Println("Advertencia: No se encontró archivo .env local, dependiendo de variables del sistema.")
	}

	cfg := &AppConfig{
		InternalAPIToken:       os.Getenv("INTERNAL_API_TOKEN"),
		CopernicusClientID:     os.Getenv("COPERNICUS_CLIENT_ID"),
		CopernicusClientSecret: os.Getenv("COPERNICUS_CLIENT_SECRET"),
		WorkerMode:             os.Getenv("WORKER_MODE"),
	}

	// Sistema de seguridad: Fallback a mock si la variable está vacía
	if cfg.WorkerMode == "" {
		cfg.WorkerMode = "mock"
	}

	log.Println("Configuración cargada exitosamente.")
	return cfg

}
