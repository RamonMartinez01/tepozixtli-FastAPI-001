// tepozixtli/worker/internal/repository/db.go
package db

import (
	"database/sql"
	"fmt"

	"tepozixtli-worker/internal/config"

	_ "github.com/lib/pq" // Importación anónima para el driver
)

// ConnectDB inicia la conexión con la bóveda de datos
func ConnectDB(cfg *config.AppConfig) (*sql.DB, error) {
	dsn := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		cfg.PostgresHost, cfg.PostgresPort, cfg.PostgresUser, cfg.PostgresPassword, cfg.PostgresDB)

	db, err := sql.Open("postgres", dsn)
	if err != nil {
		return nil, err
	}

	// Comprobamos el pulso de la base de datos
	if err = db.Ping(); err != nil {
		return nil, err
	}

	return db, nil
}

// GetGeometryGeoJSON busca el polígono por ID dinámicamente según el tipo de entidad
func GetGeometryGeoJSON(db *sql.DB, entidadTipo string, entidadID string) (string, error) {
	// 1. Mapeo Seguro (Whitelist) para evitar vulnerabilidades de inyección SQL
	var nombreTabla string
	var nombreColumna string

	switch entidadTipo {
	case "municipio":
		nombreTabla = "municipios" 
		nombreColumna = "cvegeo" // La clave de 5 dígitos
	case "region":
		nombreTabla = "regiones"
		nombreColumna = "region_id"
	case "entidad_federativa", "estado": // Aceptamos ambos términos por retrocompatibilidad
        nombreTabla = "entidades_federativas"
		nombreColumna = "cve_ent" // La clave de 2 dígitos
	default:
		return "", fmt.Errorf("operación abortada: tipo de entidad no reconocido [%s]", entidadTipo)
	}

	// 2. Construcción Dinámica de la Query
    // fmt.Sprintf ES SEGURO aquí porque nombreTabla y nombreColumna jamás vienen del usuario,
    // están estrictamente controlados por nuestro switch. El valor (entidadID) sí va parametrizado ($1).
    query := fmt.Sprintf(`SELECT ST_AsGeoJSON(geom) FROM %s WHERE %s = $1`, nombreTabla, nombreColumna)

	var geojson string
	err := db.QueryRow(query, entidadID).Scan(&geojson)
	if err != nil {
		return "", fmt.Errorf("error obteniendo geometría de la tabla %s (buscando %s = %s): %v", nombreTabla, nombreColumna, entidadID, err)
	}

	return geojson, nil
}
