// tepozixtli/worker/internal/processor/translator.go
package processor

import (
	"fmt"
	"log"
	"os/exec"
	"path/filepath"
	"strings"
)

// ConvertToCOG toma la ruta de un archivo TIFF crudo y genera una versión Cloud Optimized.
// Retorna la ruta física del nuevo archivo generado.
func ConvertToCOG(inputPath string) (string, error) {
	// 1. Definir el nombre del archivo de salida
	// Cambiamos el prefijo "raw_" por "cog_" para distinguirlos en la carpeta staging
	dir := filepath.Dir(inputPath)
	base := filepath.Base(inputPath)
	outName := strings.Replace(base, "raw_", "cog_", 1)
	outputPath := filepath.Join(dir, outName)

	log.Printf("[TRANSLATOR] Transformando %s a formato COG...", base)

	// 2. Construir el comando gdal_translate
	// -of COG: Le dice a GDAL que genere internamente los "tiles" y "overviews" (pirámides).
	// -co COMPRESS=DEFLATE: Comprime el archivo sin perder calidad (Lossless) para ahorrar red.
	cmd := exec.Command("gdal_translate",
		"-of", "COG",
		"-co", "COMPRESS=DEFLATE",
		inputPath,
		outputPath,
	)

	// 3. Ejecutar el comando en el sistema operativo del contenedor (Debian)
	// CombinedOutput captura cualquier error o mensaje que GDAL imprima en la consola de Linux
	output, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("error ejecutando gdal_translate: %v, consola: %s", err, string(output))
	}

	log.Printf("[TRANSLATOR] COG generado exitosamente: %s", outName)
	return outputPath, nil
}
