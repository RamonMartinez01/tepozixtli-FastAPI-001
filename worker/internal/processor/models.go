// tepozixtli/worker/internal/processor/models.go
package processor

// Raster representa los datos puros extraídos del archivo TIFF.
// Es 100% independiente de GDAL.
type Raster struct {
	Width  int
	Height int
	Data   [][]float64 // Nuestra matriz de valores
}

// AnalysisResult contiene los cálculos finales que enviaremos a FastAPI.
type AnalysisResult struct {
	Indicador string  `json:"indicador"`
	Minimo    float64 `json:"minimo"`
	Maximo    float64 `json:"maximo"`
	Promedio  float64 `json:"promedio"`
	// Más adelante podemos agregar histogramas o conteo de píxeles válidos
}
