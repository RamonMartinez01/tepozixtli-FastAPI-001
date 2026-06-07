// tepozixtli/worker/internal/processor/decoder.go
package processor

import (
	"fmt"

	"github.com/lukeroth/gdal"
)

// DecodeTIFF lee un archivo .tiff usando GDAL y lo convierte en nuestra estructura Raster.
func DecodeTIFF(filepath string) (*Raster, error) {
	// 1. Abrir el dataset en modo solo lectura de forma segura
	dataset, err := gdal.Open(filepath, gdal.ReadOnly)
	if err != nil {
		return nil, fmt.Errorf("no se pudo abrir el archivo TIFF o no es un dataset válido: %w", err)
	}
	// Es crítico liberar el dataset al terminar para evitar fugas de memoria (memory leaks) en C
	defer dataset.Close()

	// 2. Obtener la primera banda del raster
	band := dataset.RasterBand(1)

	// 3. Extraer las dimensiones geométricas de la imagen
	width := band.XSize()
	height := band.YSize()

	// 4. Asignar un buffer plano (unidimensional) para la lectura de alto rendimiento
	buffer := make([]float64, width*height)

	// 5. Ejecutar la operación de lectura de E/S
	// Nota: Usamos '=' y no ':=' porque 'err' ya fue declarada en el paso 1
	err = band.IO(gdal.Read, 0, 0, width, height, buffer, width, height, 0, 0)
	if err != nil {
		return nil, fmt.Errorf("error de lectura I/O en la banda del raster: %w", err)
	}

	// 6. Transformar el buffer plano en nuestra estructura de matriz bidimensional
	matrix := make([][]float64, height)
	for y := 0; y < height; y++ {
		matrix[y] = make([]float64, width)
		for x := 0; x < width; x++ {
			matrix[y][x] = buffer[y*width+x]
		}
	}

	// 7. Construir y retornar nuestro Raster
	return &Raster{
		Width:  width,
		Height: height,
		Data:   matrix,
	}, nil
}
