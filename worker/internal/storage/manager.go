// tepozixtli/worker/internal/storage/manager.go
package storage

import (
	"fmt"
	"os"
	"path/filepath"
)

// StagingPath es la ruta donde guardaremos los archivos temporales
const StagingPath = "data/staging"

// SaveTiff guarda el slice de bytes en la ruta de staging definida
func SaveTiff(data []byte, fileName string) error {
	// Aseguramos que la carpeta exista (por si acaso)
	if err := os.MkdirAll(StagingPath, 0755); err != nil {
		return fmt.Errorf("error creando directorio de staging: %w", err)
	}

	// Construimos la ruta completa: data/staging/nombre_archivo.tiff
	fullPath := filepath.Join(StagingPath, fileName)

	// Escribimos el archivo
	return os.WriteFile(fullPath, data, 0644)
}
