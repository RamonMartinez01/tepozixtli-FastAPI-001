// tepozixtli/worker/internal/processor/engine_test.go
package processor

import (
	"testing"
)

func TestCalculateStats(t *testing.T) {
	// 1. Preparamos nuestro Raster falso (El Simulacro)
	// Una matriz simple de 3x3
	mockRaster := &Raster{
		Width:  3,
		Height: 3,
		Data: [][]float64{
			{0.1, 0.2, 0.3},
			{0.4, 0.5, 0.6},
			{0.7, 0.8, 0.9},
		},
	}

	// 2. Ejecutamos el motor que acabamos de programar
	resultado, err := CalculateStats(mockRaster, "NDVI_MOCK")

	// 3. Verificamos que no haya errores
	if err != nil {
		t.Fatalf("El motor devolvió un error inesperado: %v", err)
	}

	// 4. Verificamos las matemáticas (Afirmaciones / Assertions)
	if resultado.Minimo != 0.1 {
		t.Errorf("Error en Mínimo: Esperaba 0.1, obtuve %v", resultado.Minimo)
	}

	if resultado.Maximo != 0.9 {
		t.Errorf("Error en Máximo: Esperaba 0.9, obtuve %v", resultado.Maximo)
	}

	if resultado.Promedio != 0.5 {
		t.Errorf("Error en Promedio: Esperaba 0.5, obtuve %v", resultado.Promedio)
	}
}
