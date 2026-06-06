// tepozixtli/worker/copernicus/auth.go
package copernicus

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"
)

// URL oficial del servidor de autenticación de Copernicus
const tokenURL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

// TokenResponse mapea el JSON exacto que devuelve el servidor de Copernicus
type TokenResponse struct {
	AccessToken      string `json:"access_token"`
	ExpiresIn        int    `json:"expires_in"`
	RefreshExpiresIn int    `json:"refresh_expires_in"`
	TokenType        string `json:"token_type"`
}

// Authenticator maneja la obtención y el caché seguro en memoria
type Authenticator struct {
	clientID     string
	clientSecret string
	token        string
	expiresAt    time.Time
	mu           sync.RWMutex // Protege el caché para acceso concurrente seguro
}

// NewAuthenticator es el constructor de nuestro cliente
func NewAuthenticator(id, secret string) *Authenticator {
	return &Authenticator{
		clientID:     id,
		clientSecret: secret,
	}
}

// GetToken devuelve el token en caché si es válido, o solicita uno nuevo a CDSE
func (a *Authenticator) GetToken() (string, error) {
	// 1. Lectura rápida del caché (Bloqueo de lectura)
	a.mu.RLock()
	// Verificamos si hay token y si le sobra más de 1 minuto de vida por seguridad
	if a.token != "" && time.Now().Before(a.expiresAt.Add(-1*time.Minute)) {
		validToken := a.token
		a.mu.RUnlock()
		return validToken, nil
	}
	a.mu.RUnlock()

	// 2. Si el token expiró o no existe, bloqueamos el acceso para escritura
	a.mu.Lock()
	defer a.mu.Unlock()

	// Doble comprobación: otra rutina pudo haber renovado el token mientras esperábamos el candado
	if a.token != "" && time.Now().Before(a.expiresAt.Add(-1*time.Minute)) {
		return a.token, nil
	}

	// 3. Preparamos el payload (x-www-form-urlencoded)
	data := url.Values{}
	data.Set("client_id", a.clientID)
	data.Set("client_secret", a.clientSecret)
	data.Set("grant_type", "client_credentials")

	req, err := http.NewRequest("POST", tokenURL, strings.NewReader(data.Encode()))
	if err != nil {
		return "", fmt.Errorf("error creando request HTTP: %v", err)
	}
	req.Header.Add("Content-Type", "application/x-www-form-urlencoded")

	// 4. Ejecutamos la petición HTTP con límite de tiempo
	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("error contactando al servidor de Copernicus: %v", err)
	}
	defer resp.Body.Close()

	// Verificamos si Copernicus rechazó las credenciales
	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("credenciales rechazadas (HTTP %d): %s", resp.StatusCode, string(bodyBytes))
	}

	// 5. Decodificamos el JSON entrante
	var tokenRes TokenResponse
	if err := json.NewDecoder(resp.Body).Decode(&tokenRes); err != nil {
		return "", fmt.Errorf("error decodificando respuesta JSON: %v", err)
	}

	// 6. Actualizamos el caché y calculamos la nueva fecha de expiración
	a.token = tokenRes.AccessToken
	a.expiresAt = time.Now().Add(time.Duration(tokenRes.ExpiresIn) * time.Second)

	return a.token, nil
}
