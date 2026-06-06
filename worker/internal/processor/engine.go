// tepozixtli/worker/internal/processor/engine.go
package processor

import (
	"errors"
)

// CalculateStats recorre la matriz y calcula los valores según el indicador (NDVI, etc.)
func CalculateStats(raster *Raster, indicador string) (*AnalysisResult, error) {
	// 1. Validación de seguridad para evitar pánicos (segmentation faults)
	if raster == nil || len(raster.Data) == 0 || len(raster.Data[0]) == 0 {
		return nil, errors.New("el raster está vacío o es inválido")
	}

	// 2. Inicializamos nuestras variables asumiendo que el primer pixel es el min y el max
	min := raster.Data[0][0]
	max := raster.Data[0][0]
	sum := 0.0
	count := 0

	// 3. Recorremos la matriz bidimensional
	for _, row := range raster.Data {
		for _, val := range row {
			if val < min {
				min = val
			}
			if val > max {
				max = val
			}
			sum += val
			count++
		}
	}

	// 4. Calculamos el promedio
	promedio := sum / float64(count)

	// 5. Empaquetamos y retornamos el resultado
	return &AnalysisResult{
		Indicador: indicador,
		Minimo:    min,
		Maximo:    max,
		Promedio:  promedio,
	}, nil
}
