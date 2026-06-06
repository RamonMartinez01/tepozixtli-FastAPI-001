// tepozixtli/worker/internal/processor/decoder.go
package processor

import (
	"errors"
)

// DecodeTIFF lee un archivo .tiff usando GDAL y lo convierte en nuestra estructura Raster.
func DecodeTIFF(filepath string) (*Raster, error) {
	// TODO: Fase 3 - Implementar la lectura con GDAL (CGO)

	// Retornamos un error por ahora para que compile y nos recuerde que falta lógica
	return nil, errors.New("not implemented: DecodeTIFF")
}
