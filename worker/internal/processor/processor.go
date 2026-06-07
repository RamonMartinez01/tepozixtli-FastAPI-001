// tepozixtli/worker/internal/processor/processor.go
package processor

import (
	"fmt"
	"log"
)

// ProcessTIFF coordina la decodificación del archivo y el cálculo matemático.
func ProcessTIFF(filepath string, indicador string) (*AnalysisResult, error) {
	log.Printf("[PROCESSOR] Iniciando decodificación de: %s\n", filepath)

	// 1. Decodificar (Fase 3)
	raster, err := DecodeTIFF(filepath)
	if err != nil {
		return nil, fmt.Errorf("error al decodificar el TIFF: %w", err)
	}

	log.Printf("[PROCESSOR] Decodificación exitosa. Matriz extraída: %dx%d píxeles.\n", raster.Width, raster.Height)
	log.Printf("[PROCESSOR] Ejecutando cálculo de indicador: %s\n", indicador)

	// 2. Calcular (Fase 4)
	resultado, err := CalculateStats(raster, indicador)
	if err != nil {
		return nil, fmt.Errorf("error calculando estadísticas: %w", err)
	}

	log.Printf("[PROCESSOR] Cálculo completado. Min: %.4f, Max: %.4f, Promedio: %.4f\n", resultado.Minimo, resultado.Maximo, resultado.Promedio)

	return resultado, nil
}
