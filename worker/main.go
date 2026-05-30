// tepozixtli/worker/main.go
package main

import (
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"tepozixtli-worker/config"
	"tepozixtli-worker/copernicus"
)

func main() {
	fmt.Println("Iniciando Ingestor Satelital (Worker en Go)...")

	// Cargamos la configuración desde la raíz
	cfg := config.LoadConfig()

	// Validación de seguridad inicial
	if cfg.InternalAPIToken == "" {
		log.Fatal("ERROR CRÍTICO: INTERNAL_API_TOKEN no está definido. El Worker no podrá comunicarse con la API.")
	}
	if cfg.CopernicusClientID == "" || cfg.CopernicusClientSecret == "" {
		log.Fatal("ERROR CRÍTICO: Credenciales de Copernicus incompletas en el .env")
	}

	fmt.Println("Configuración y credenciales base detectadas.")

	// Inicializamos el sistema de autenticación
	auth := copernicus.NewAuthenticator(cfg.CopernicusClientID, cfg.CopernicusClientSecret)

	// Creamos un canal para interceptar las señales de terminación del Sistema Operativo
	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

	// Configuración del Ticker (El "Corazón" del Daemon)
	// Para nuestra prueba, configuramos un latido cada 15 segundos
	ticker := time.NewTicker(15 * time.Second)
	// Aseguramos que el ticker se limpie de la memoria al salir de la función
	defer ticker.Stop()

	fmt.Println("Motor del Ingestor encendido. Entrando en ciclo de ejecución continua...")

	// 4. El Bucle Principal de Eventos (Event Loop)
	for {
		// La sentencia 'select' bloquea la ejecución hasta que uno de sus 'cases' reciba un mensaje
		select {
		case <-ticker.C:
			// --- SECCIÓN DE TRABAJO ---
			// Este bloque se ejecutará cada vez que el Ticker envíe un pulso
			fmt.Println("\n--- [LATIDO] Ejecutando ciclo de ingesta ---")
			fmt.Println("Verificando/Renovando enlace con Copernicus CDSE...")

			token, err := auth.GetToken()
			if err != nil {
				// Usamos log.Printf en lugar de log.Fatal para NO matar el daemon si la red falla un segundo
				log.Printf("Fallo en la autenticación durante el ciclo: %v", err)
				continue
			}

			preview := token
			if len(token) > 15 {
				preview = token[:15]
			}
			fmt.Printf("Enlace activo. Token actual: %s...\n", preview)
			fmt.Println("Esperando el próximo ciclo...")

		case sig := <-sigs:
			// --- SECCIÓN DE APAGADO ---
			// Este bloque se ejecuta si Docker hace 'stop' o si presionas Ctrl+C
			fmt.Printf("\n[SISTEMA] Señal de apagado detectada: %v\n", sig)
			fmt.Println("Iniciando secuencia de apagado elegante (Graceful Shutdown)...")

			// Aquí en el futuro cerraremos conexiones y limpiaremos memoria

			fmt.Println("Worker detenido de forma segura. Cambio y fuera.")
			os.Exit(0) // Código 0 indica un apagado limpio y sin errores
		}
	}
}
