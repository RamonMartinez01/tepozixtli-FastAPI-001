// tepozixtli/worker/internal/config/loader.go
package config

import (
	"log"
	"os"

	"github.com/joho/godotenv"
)

// AppConfig almacena las variables de entorno de nuestra aplicación
type AppConfig struct {
	RedisHost              string
	RedisPort              string
	RedisPassword          string
	InternalAPIToken       string
	CopernicusClientID     string
	CopernicusClientSecret string
	WorkerMode             string
	PostgresHost           string
	PostgresPort           string
	PostgresUser           string
	PostgresPassword       string
	PostgresDB             string
}

// LoadConfig lee el archivo .env y mapea las variables a la estructura AppConfig
func LoadConfig() *AppConfig {
	// Subimos un nivel desde /worker para leer el .env en la raíz
	err := godotenv.Load("../.env")
	if err != nil {
		log.Println("Advertencia: No se encontró archivo .env local, dependiendo de variables del sistema.")
	}

	cfg := &AppConfig{
		RedisHost:              os.Getenv("REDIS_HOST"),
		RedisPort:              os.Getenv("REDIS_PORT"),
		RedisPassword:          os.Getenv("REDIS_PASSWORD"),
		InternalAPIToken:       os.Getenv("INTERNAL_API_TOKEN"),
		CopernicusClientID:     os.Getenv("COPERNICUS_CLIENT_ID"),
		CopernicusClientSecret: os.Getenv("COPERNICUS_CLIENT_SECRET"),
		WorkerMode:             os.Getenv("WORKER_MODE"),
		PostgresHost:           os.Getenv("DB_HOST"),
		PostgresPort:           os.Getenv("DB_PORT"),
		PostgresUser:           os.Getenv("POSTGRES_USER"),
		PostgresPassword:       os.Getenv("POSTGRES_PASSWORD"),
		PostgresDB:             os.Getenv("POSTGRES_DB"),
	}

	// Sistema de seguridad: Fallback a mock si la variable está vacía
	if cfg.WorkerMode == "" {
		cfg.WorkerMode = "mock"
	}

	log.Println("Configuración cargada exitosamente.")
	return cfg

}
