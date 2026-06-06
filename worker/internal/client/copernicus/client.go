// tepozixtli/worker/internal/client/copernicus/client.go
package copernicus

import (
	"bytes"
	"fmt"
	"io"
	"net/http"
	"time"
)

// CopernicusClient encapsula la autenticación y la lógica de peticiones
type CopernicusClient struct {
	auth *Authenticator
}

// NewClient crea un cliente nuevo
func NewClient(auth *Authenticator) *CopernicusClient {
	return &CopernicusClient{auth: auth}
}

// FetchProcessingData construye el payload, obtiene el token y dispara la petición.
// Retorna los bytes del archivo (el TIFF) o un error.
func (c *CopernicusClient) FetchProcessingData(geometryGeoJSON, fechaCaptura, indicador string) ([]byte, error) {
	// 1. Obtener token
	token, err := c.auth.GetToken()
	if err != nil {
		return nil, fmt.Errorf("error obteniendo token: %w", err)
	}

	// 2. Construir Payload (usando la fábrica que ya tenemos)
	payloadBytes, err := BuildProcessingPayload(geometryGeoJSON, fechaCaptura, indicador)
	if err != nil {
		return nil, fmt.Errorf("error construyendo payload: %w", err)
	}

	// 3. Preparar petición
	processURL := "https://sh.dataspace.copernicus.eu/api/v1/process"
	req, err := http.NewRequest("POST", processURL, bytes.NewBuffer(payloadBytes))
	if err != nil {
		return nil, fmt.Errorf("error creando request: %w", err)
	}

	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "image/tiff")

	// 4. Disparo
	client := &http.Client{Timeout: 3 * time.Minute}
	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("error en petición HTTP: %w", err)
	}
	defer resp.Body.Close()

	// 5. Validar respuesta
	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("error de API (Status %d): %s", resp.StatusCode, string(bodyBytes))
	}

	// 6. Leer y retornar bytes
	return io.ReadAll(resp.Body)
}
