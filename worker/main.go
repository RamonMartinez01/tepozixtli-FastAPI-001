// tepozixtli/worker/main.go
package main

import (
	"fmt"
	"log"

	// Importamos el módulo local que creamos
	"tepozixtli-worker/config"
)

func main() {
	fmt.Println("Iniciando Ingestor Satelital (Worker en Go)...")

	// Cargamos la configuración desde la raíz
	cfg := config.LoadConfig()

	// Validación de seguridad inicial
	if cfg.InternalAPIToken == "" {
		log.Fatal("ERROR CRÍTICO: INTERNAL_API_TOKEN no está definido. El Worker no podrá comunicarse con la API.")
	}

	fmt.Println("Configuración cargada exitosamente.")
	fmt.Println("Token de seguridad interno detectado. El Ingestor está listo para operar.")
}