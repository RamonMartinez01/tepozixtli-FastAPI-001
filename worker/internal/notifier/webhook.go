// tepozixtli/worker/internal/notifier/webhook.go
package notifier

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"time"

	"tepozixtli-worker/internal/config"
)

// WebhookPayload es el molde exacto que espera FastAPI (IndicadorMacroCreate)
type WebhookPayload struct {
	TipoIndicador string `json:"tipo_indicador"`
	EntidadTipo   string `json:"entidad_tipo"`
	EntidadID     string `json:"entidad_id"`
	FechaCaptura  string `json:"fecha_captura"`
	CogURL        string `json:"cog_url"`
}

// SendCOGReadyNotification dispara el POST hacia la API
func SendCOGReadyNotification(cfg *config.AppConfig, payload WebhookPayload) error {
	log.Println("[NOTIFIER] Preparando notificación de Webhook para FastAPI...")

	// 1. Convertir nuestra estructura a JSON
	jsonData, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("error serializando payload de webhook: %w", err)
	}

	// 2. Construir la URL del endpoint (usamos el nombre del contenedor 'api' en Docker)
	// Ajusta el puerto interno si tu FastAPI no escucha en el 8000 dentro del contenedor
	apiURL := "http://api:8000/api/v1/indicadores-macro/webhook/indicador-macro"

	// 3. Crear la petición HTTP POST
	req, err := http.NewRequest("POST", apiURL, bytes.NewBuffer(jsonData))
	if err != nil {
		return fmt.Errorf("error creando petición HTTP: %w", err)
	}

	// 4. Configurar cabeceras
	req.Header.Set("Content-Type", "application/json")
	// Usamos el token interno que ya tenías validado en tu main.go para seguridad
	if cfg.InternalAPIToken != "" {
		req.Header.Set("Authorization", "Bearer "+cfg.InternalAPIToken)
	}

	// 5. Ejecutar el disparo con un timeout razonable
	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("error conectando con FastAPI: %w", err)
	}
	defer resp.Body.Close()

	// 6. Validar la respuesta de FastAPI
	if resp.StatusCode != http.StatusCreated && resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("FastAPI rechazó el webhook. Código: %d, Respuesta: %s", resp.StatusCode, string(bodyBytes))
	}

	log.Println("[NOTIFIER] ¡Notificación entregada exitosamente! FastAPI ha guardado el registro.")
	return nil
}
