// tepozixtli/worker/main.go
package main

import (
	"fmt"
	"log"

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

	// 3. Inicializamos el sistema de autenticación
	auth := copernicus.NewAuthenticator(cfg.CopernicusClientID, cfg.CopernicusClientSecret)

	// 4. Prueba de Fuego: Obtener el pasaporte
	fmt.Println("Solicitando enlace seguro con Copernicus Data Space Ecosystem (CDSE)...")
	token, err := auth.GetToken()
	if err != nil {
		log.Fatalf("Fallo crítico en la autenticación: %v", err)
	}

	// 5. Verificación visual segura
	// Muestra solo los primeros 15 caracteres del token
	preview := token
	if len(token) > 15 {
		preview = token[:15]
	}
	fmt.Printf("¡Enlace establecido exitosamente! Token OAuth obtenido: %s...\n", preview)
	fmt.Println("El Ingestor está listo para comenzar a descargar telemetría satelital.")
}
