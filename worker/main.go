// tepozixtli/worker/main.go
package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"tepozixtli-worker/config"
	"tepozixtli-worker/copernicus"
	"tepozixtli-worker/db"

	"github.com/redis/go-redis/v9"
)

var ctx = context.Background()

// TaskPayload es el molde exacto del JSON que FastAPI nos envía por Redis
type TaskPayload struct {
	Task          string `json:"task"`
	TipoIndicador string `json:"tipo_indicador"`
	EntidadTipo   string `json:"entidad_tipo"`
	EntidadID     string `json:"entidad_id"`
	FechaCaptura  string `json:"fecha_captura"`
}

func main() {
	fmt.Println("Iniciando Ingestor Satelital (Worker en Go)...")
	// Cargamos la configuración desde la raíz
	cfg := config.LoadConfig()

	// =======================================================
	// VALIDACIONES DE SEGURIDAD
	// =======================================================
	if cfg.InternalAPIToken == "" {
		log.Fatal("ERROR CRÍTICO: INTERNAL_API_TOKEN no está definido. El Worker no podrá comunicarse con la API.")
	}
	if cfg.CopernicusClientID == "" || cfg.CopernicusClientSecret == "" {
		log.Fatal("ERROR CRÍTICO: Credenciales de Copernicus incompletas en el .env")
	}

	fmt.Printf(">>> MODO DE OPERACIÓN DEL WORKER: [%s] <<<\n", cfg.WorkerMode)

	// =======================================================
	// INICIALIZAR AUTENTICADOR
	// =======================================================
	var auth *copernicus.Authenticator

	if cfg.WorkerMode == "live" {
		auth = copernicus.NewAuthenticator(cfg.CopernicusClientID, cfg.CopernicusClientSecret)
		fmt.Println("Configuración y credenciales base detectadas.")
	}

	// =======================================================
	// CONEXIÓN A POSTGRESQL
	// =======================================================
	pgDB, err := db.ConnectDB(cfg)
	if err != nil {
		log.Fatalf("ERROR CRÍTICO: No se pudo conectar a PostgreSQL: %v", err)
	}
	defer pgDB.Close()
	fmt.Println("Conexión con PostgreSQL Bóveda Central establecida.")

	// =======================================================
	// CONEXIÓN A REDIS
	// =======================================================
	rdb := redis.NewClient(&redis.Options{
		Addr:     fmt.Sprintf("%s:%s", cfg.RedisHost, cfg.RedisPort),
		Password: cfg.RedisPassword,
		DB:       0,
	})
	if _, err := rdb.Ping(ctx).Result(); err != nil {
		log.Fatalf("ERROR CRÍTICO: No se pudo conectar a Redis: %v", err)
	}
	fmt.Println("Conexión con Redis Broker establecida.")

	// =======================================================
	// CANALES DE CONTROL Y OYENTE ASÍNCRONO
	// =======================================================
	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

	// Este canal conectará a nuestro "oyente" de Redis con el motor principal
	tasks := make(chan string)

	// EL OYENTE ASÍNCRONO (Goroutine)
	// Esto corre en segundo plano y se queda bloqueado (BLPOP) hasta que llegue algo
	go func() {
		for {
			result, err := rdb.BLPop(ctx, 0, "queue:copernicus_tasks").Result()
			if err != nil {
				log.Printf("Error leyendo de Redis: %v", err)
				continue
			}
			// result[0] es el nombre de la cola, result[1] es el payload
			tasks <- result[1] // Enviamos el mensaje al bucle principal
		}
	}()

	fmt.Println("Motor del Ingestor encendido. Esperando tareas en la cola...")

	// =======================================================
	//  EL BUCLE PRINCIPAL DE EVENTOS
	// =======================================================
	for {
		select {
		case taskPayload := <-tasks:
			// --- SECCIÓN DE TRABAJO (Cuando llega un mensaje de Redis) ---
			fmt.Printf("\n--- [NUEVA TAREA RECIBIDA] ---\nPayload: %s\n", taskPayload)

			// Paso A: Desempacar el JSON
			var payload TaskPayload
			if err := json.Unmarshal([]byte(taskPayload), &payload); err != nil {
				log.Printf("Error decodificando payload JSON: %v", err)
				continue // Ignoramos mensajes corruptos y seguimos escuchando
			}

			// Paso B: Extraer la geometría de nuestra base de datos
			fmt.Printf("Extrayendo geometría espacial para %s [%s]...\n", payload.EntidadTipo, payload.EntidadID)

			geojson, err := db.GetGeometryGeoJSON(pgDB, payload.EntidadTipo, payload.EntidadID)
			if err != nil {
				log.Printf("Fallo extrayendo geometría de la DB: %v", err)
				continue
			}

			// Imprimimos solo un fragmento del GeoJSON para no inundar la consola
			previewGeo := geojson
			if len(geojson) > 60 {
				previewGeo = geojson[:60] + "..."
			}
			fmt.Printf("ÉXITO: Geometría obtenida. (Fragmento: %s)\n", previewGeo)

			// BIFURCACIÓN LÓGICA SEGÚN EL MODO
			if cfg.WorkerMode == "mock" {
				fmt.Println("[MOCK] Simulando extracción de datos (AISLADO de CDSE)...")
				fmt.Println("[MOCK] Tarea procesada localmente con éxito.")
				continue
			}

			// BLOQUE LIVE
			fmt.Println("Verificando/Renovando enlace con Copernicus CDSE...")
			token, err := auth.GetToken()
			if err != nil {
				log.Printf("Fallo en la autenticación durante el ciclo: %v", err)
				continue
			}

			preview := token
			if len(token) > 15 {
				preview = token[:15]
			}
			fmt.Printf("Enlace activo. Token actual: %s...\n", preview)
			fmt.Println("Listo para iniciar descarga desde Statistical API...")

			// ===================================================
			// INICIO DEL BLOQUE DE EXTRACCIÓN A COPERNICUS
			// ===================================================
			fmt.Println("Ensamblando Payload en la fábrica para Processing API...")

			// 1. Usamos nuestra fábrica para construir el JSON exacto.
			payloadBytes, err := copernicus.BuildProcessingPayload(geojson, payload.FechaCaptura, payload.TipoIndicador)
			if err != nil {
				log.Printf("ERROR: Falló la construcción del payload de procesamiento: %v\n", err)
				continue // Usamos continue para no apagar el Worker, solo abortamos esta tarea
			}

			// 2. Apuntamos a la Processing API de Copernicus
			processURL := "https://sh.dataspace.copernicus.eu/api/v1/process"
			req, err := http.NewRequest("POST", processURL, bytes.NewBuffer(payloadBytes))
			if err != nil {
				log.Printf("ERROR: No se pudo crear la petición HTTP: %v\n", err)
				continue
			}

			// 3. Credenciales y Contratos (Headers)
			req.Header.Set("Authorization", "Bearer "+token)
			req.Header.Set("Content-Type", "application/json")
			req.Header.Set("Accept", "image/tiff") // Fundamental: pedimos un archivo matricial/binario

			// 4. Ejecución del Disparo (Con Timeout táctico)
			fmt.Println("Disparando petición a Processing API de Copernicus... (Descargando matriz de píxeles)")

			client := &http.Client{
				Timeout: 3 * time.Minute, // Damos tiempo suficiente para el procesamiento espacial
			}

			resp, err := client.Do(req)
			if err != nil {
				log.Printf("ERROR: El disparo HTTP a Copernicus falló: %v\n", err)
				continue
			}

			// 5. Análisis de la Respuesta
			bodyBytes, err := io.ReadAll(resp.Body)
			resp.Body.Close() // Cerramos el body aquí mismo por seguridad de memoria

			if err != nil {
				log.Printf("ERROR leyendo el cuerpo de la respuesta: %v\n", err)
				continue
			}

			fmt.Printf("--- RECEPCIÓN DE DATOS ---\n")
			fmt.Printf("CÓDIGO DE ESTADO HTTP: %d\n", resp.StatusCode)

			// Si es 200 OK, coronamos. Si es diferente, analizamos el motivo.
			if resp.StatusCode == 200 {
				fmt.Println("ÉXITO: ¡Archivo TIFF (Píxeles crudos) recibido!")

				// IMPORTANTE: Guardamos el archivo binario en disco
				// Usamos el ID de la entidad y la fecha para que no se sobreescriban
				fileName := fmt.Sprintf("raw_%s_%s_%s.tiff", payload.TipoIndicador, payload.EntidadID, payload.FechaCaptura)

				err := os.WriteFile(fileName, bodyBytes, 0644)
				if err != nil {
					log.Printf("ERROR guardando el TIFF en disco: %v\n", err)
				} else {
					fmt.Printf("Archivo TIFF guardado correctamente en la raíz como: %s\n", fileName)
					fmt.Printf("   Tamaño del archivo: %d bytes\n\n", len(bodyBytes))

					// TODO: Aquí implementaremos la conversión de TIFF a ArrayBuffer/JSON
				}

			} else {
				fmt.Println("ALERTA: Copernicus rechazó la petición.")
				fmt.Printf("MOTIVO: %s\n\n", string(bodyBytes))
			}
			// ===================================================
			// FIN DEL BLOQUE DE EXTRACCIÓN
			// ===================================================

		case sig := <-sigs:
			// --- SECCIÓN DE APAGADO ---
			fmt.Printf("\n[SISTEMA] Señal de apagado detectada: %v\n", sig)
			fmt.Println("Iniciando secuencia de apagado elegante (Graceful Shutdown)...")

			// Limpiamos la conexión a Redis antes de apagar
			rdb.Close()

			fmt.Println("Worker detenido de forma segura. Cambio y fuera.")
			os.Exit(0)
		}
	}
}
