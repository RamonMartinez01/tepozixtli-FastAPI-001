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

	switch entidadTipo {
	case "municipio":
		nombreTabla = "municipios" // Nombre real en tu base de datos
	case "region":
		nombreTabla = "regiones"
	case "estado":
		nombreTabla = "estados"
	default:
		return "", fmt.Errorf("operación abortada: tipo de entidad no reconocido [%s]", entidadTipo)
	}

	// 2. Construcción de la Query
	// Usar fmt.Sprintf aquí ES SEGURO porque 'nombreTabla' proviene de nuestro switch cerrado,
	// no directamente de la entrada del usuario. El ID sí va parametrizado ($1).
	query := fmt.Sprintf(`SELECT ST_AsGeoJSON(geom) FROM %s WHERE id = $1`, nombreTabla)

	var geojson string
	err := db.QueryRow(query, entidadID).Scan(&geojson)
	if err != nil {
		return "", fmt.Errorf("error obteniendo geometría de la tabla %s: %v", nombreTabla, err)
	}

	return geojson, nil
}
