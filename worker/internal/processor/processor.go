// tepozixtli/worker/internal/processor/processor.go
package processor

import (
	"fmt"
)

// ProcessTIFF coordina la decodificación del archivo y el cálculo matemático.
func ProcessTIFF(filepath string, indicador string) (*AnalysisResult, error) {
	// 1. Decodificar
	raster, err := DecodeTIFF(filepath)
	if err != nil {
		return nil, fmt.Errorf("error al decodificar el TIFF: %w", err)
	}

	// 2. Calcular
	resultado, err := CalculateStats(raster, indicador)
	if err != nil {
		return nil, fmt.Errorf("error calculando estadísticas: %w", err)
	}

	return resultado, nil
}
