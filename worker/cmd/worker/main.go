// tepozixtli/worker/cmd/worker/main.go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"

	"tepozixtli-worker/internal/client/copernicus"
	"tepozixtli-worker/internal/config"
	"tepozixtli-worker/internal/processor"
	db "tepozixtli-worker/internal/repository"
	"tepozixtli-worker/internal/storage"

	"github.com/redis/go-redis/v9"
)

var ctx = context.Background()

type TaskPayload struct {
	Task          string `json:"task"`
	TipoIndicador string `json:"tipo_indicador"`
	EntidadTipo   string `json:"entidad_tipo"`
	EntidadID     string `json:"entidad_id"`
	FechaCaptura  string `json:"fecha_captura"`
}

func main() {
	fmt.Println("Iniciando Ingestor Satelital (Worker en Go)...")
	cfg := config.LoadConfig()

	// Validaciones de seguridad
	if cfg.InternalAPIToken == "" {
		log.Fatal("ERROR CRÍTICO: INTERNAL_API_TOKEN no definido.")
	}

	fmt.Printf(">>> MODO DE OPERACIÓN: [%s] <<<\n", cfg.WorkerMode)

	// Inicialización de componentes base
	pgDB, err := db.ConnectDB(cfg)
	if err != nil {
		log.Fatalf("ERROR CRÍTICO: No se pudo conectar a PostgreSQL: %v", err)
	}
	defer pgDB.Close()

	rdb := redis.NewClient(&redis.Options{
		Addr:     fmt.Sprintf("%s:%s", cfg.RedisHost, cfg.RedisPort),
		Password: cfg.RedisPassword,
		DB:       0,
	})

	// Inicialización del cliente Copernicus (si estamos en modo live)
	var copernicusClient *copernicus.CopernicusClient
	if cfg.WorkerMode == "live" {
		if cfg.CopernicusClientID == "" || cfg.CopernicusClientSecret == "" {
			log.Fatal("ERROR CRÍTICO: Credenciales de Copernicus incompletas.")
		}
		auth := copernicus.NewAuthenticator(cfg.CopernicusClientID, cfg.CopernicusClientSecret)
		copernicusClient = copernicus.NewClient(auth)
		fmt.Println("Conexión con Copernicus inicializada.")
	}

	// Canales y Oyente de Redis
	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)
	tasks := make(chan string)

	go func() {
		for {
			result, err := rdb.BLPop(ctx, 0, "queue:copernicus_tasks").Result()
			if err != nil {
				log.Printf("Error leyendo de Redis: %v", err)
				continue
			}
			tasks <- result[1]
		}
	}()

	fmt.Println("Motor encendido. Esperando tareas...")

	// Bucle principal
	for {
		select {
		case taskPayload := <-tasks:
			fmt.Printf("\n--- [NUEVA TAREA RECIBIDA] ---\n")

			var payload TaskPayload
			if err := json.Unmarshal([]byte(taskPayload), &payload); err != nil {
				log.Printf("Error decodificando JSON: %v", err)
				continue
			}

			// 1. Obtener Geometría
			geojson, err := db.GetGeometryGeoJSON(pgDB, payload.EntidadTipo, payload.EntidadID)
			if err != nil {
				log.Printf("Fallo extrayendo geometría: %v", err)
				continue
			}

			// 2. Ejecutar según modo
			if cfg.WorkerMode == "mock" {
				fmt.Println("[MOCK] Simulación completada.")
				continue
			}

			// 3. Ejecución Real (Live)
			tiffData, err := copernicusClient.FetchProcessingData(geojson, payload.FechaCaptura, payload.TipoIndicador)
			if err != nil {
				log.Printf("ERROR EN CLIENTE: %v", err)
				continue
			}

			/// 4. Persistencia
			fileName := fmt.Sprintf("raw_%s_%s_%s.tiff", payload.TipoIndicador, payload.EntidadID, payload.FechaCaptura)

			err = storage.SaveTiff(tiffData, fileName)
			if err != nil {
				log.Printf("ERROR guardando archivo: %v", err)
				continue // Si falla el guardado, no podemos procesar. Saltamos al siguiente.
			}

			fmt.Printf("ÉXITO: Archivo guardado (%d bytes).\n", len(tiffData))

			/// 5. El Cerebro (Procesamiento Matemático)
			// Construimos la ruta exacta donde el storage guardó el archivo
			// Ajusta "data/staging" si tu storage.SaveTiff lo guarda en otra ruta relativa distinta
			fullPath := filepath.Join("data", "staging", fileName)

			fmt.Println("--- Iniciando Análisis Geoespacial ---")
			resultado, err := processor.ProcessTIFF(fullPath, payload.TipoIndicador)
			if err != nil {
				log.Printf("ERROR EN PROCESAMIENTO GDAL/MATEMÁTICO: %v", err)
				continue
			}

			fmt.Printf(">>> ANÁLISIS COMPLETADO - %s <<<\n", resultado.Indicador)
			fmt.Printf("Min: %.4f | Max: %.4f | Promedio: %.4f\n", resultado.Minimo, resultado.Maximo, resultado.Promedio)
			fmt.Println("--------------------------------------")

			// TODO: - Enviar este 'resultado' a FastAPI

		case sig := <-sigs:
			fmt.Printf("\n[SISTEMA] Apagado detectado: %v\n", sig)
			rdb.Close()
			os.Exit(0)
		}
	}
}
