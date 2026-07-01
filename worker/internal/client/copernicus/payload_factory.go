// tepozixtli/worker/internal/client/copernicus/payload_factory.go
package copernicus

import (
	"encoding/json"
	"fmt"
)

// --- MOLDES DEL PAYLOAD PARA LA PROCESSING API ---

type ProcessPayload struct {
	Input      InputPayload  `json:"input"`
	Output     OutputPayload `json:"output"`
	Evalscript string        `json:"evalscript"`
}

type InputPayload struct {
	Bounds Bounds `json:"bounds"`
	Data   []Data `json:"data"`
}

type Bounds struct {
	// json.RawMessage evita que Go convierta nuestro string GeoJSON en un string escapado (con \").
	// Lo inyecta como un objeto JSON puro.
	Geometry   json.RawMessage `json:"geometry"`
	Properties Properties      `json:"properties"`
}

type Properties struct {
	Crs string `json:"crs"`
}

type Data struct {
	Type       string     `json:"type"`
	DataFilter DataFilter `json:"dataFilter"`
}

type DataFilter struct {
	TimeRange TimeRange `json:"timeRange"`
	// Para la Processing API, a veces necesitamos añadir mosaickingOrder
	MosaickingOrder string `json:"mosaickingOrder,omitempty"`
}

type TimeRange struct {
	From string `json:"from"`
	To   string `json:"to"`
}

// NUEVO: Bloque de Output para definir qué queremos recibir
type OutputPayload struct {
	Width     int        `json:"width,omitempty"`
    Height    int        `json:"height,omitempty"`
	Responses []Response `json:"responses"`
}

type Response struct {
	Identifier string `json:"identifier"`
	Format     Format `json:"format"`
}

type Format struct {
	Type string `json:"type"` // Ej: "image/tiff"
}

// BuildStatisticalPayload ensambla los datos y genera el JSON final para enviar a Copernicus
// BuildProcessingPayload ensambla el JSON para la Processing API
func BuildProcessingPayload(geometryGeoJSON string, fechaCaptura string, indicador string) ([]byte, error) {
	// 1. Fechas
	timeFrom := fmt.Sprintf("%sT00:00:00Z", fechaCaptura)
	timeTo := fmt.Sprintf("%sT23:59:59Z", fechaCaptura)

	// 2. Selección de Colección y Evalscript
	var datasetType string
	var evalscript string

	switch indicador {
	case "LST":
		datasetType = "sentinel-3-slstr"
		evalscript = `//VERSION=3
		function setup() {
			return {
				input: [{ bands: ["S8", "dataMask"] }],
				output: [{ id: "default", bands: 1, sampleType: "FLOAT32" }]
			};
		}
		function evaluatePixel(sample) {
			// La banda S8 captura la emisión térmica infrarroja (Temperatura en Kelvin)
			// Multiplicamos por la máscara para que los píxeles sin datos sean 0
			if (sample.dataMask === 0) {
				return [0];
			}
			return [sample.S8];
		}`
	case "NDVI":
		datasetType = "sentinel-2-l2a"
		evalscript = `//VERSION=3 ...`
	default:
		return nil, fmt.Errorf("indicador no soportado: %s", indicador)
	}

	// 3. Ensamblaje del Payload (Aquí estamos "usando" las variables)
	payload := ProcessPayload{
		Input: InputPayload{
			Bounds: Bounds{
				Geometry:   json.RawMessage(geometryGeoJSON),
				Properties: Properties{Crs: "http://www.opengis.net/def/crs/EPSG/0/4326"},
			},
			Data: []Data{
				{
					Type: datasetType,
					DataFilter: DataFilter{
						TimeRange:       TimeRange{From: timeFrom, To: timeTo},
						MosaickingOrder: "leastCC",
					},
				},
			},
		},
		Output: OutputPayload{
			Width: 1024,
			Responses: []Response{
				{
					Identifier: "default",
					Format:     Format{Type: "image/tiff"},
				},
			},
		},
		Evalscript: evalscript,
	}

	return json.MarshalIndent(payload, "", "  ")
}
