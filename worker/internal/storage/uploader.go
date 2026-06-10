// tepozixtli/worker/internal/storage/uploader.go
package storage

import (
	"context"
	"fmt"
	"log"
	"os"

	"tepozixtli-worker/internal/config"

	"github.com/aws/aws-sdk-go-v2/aws"
	awsconfig "github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/aws/aws-sdk-go-v2/service/s3/types"
)

// UploadCOG sube el archivo a DigitalOcean Spaces y retorna su URL pública
func UploadCOG(ctx context.Context, appCfg *config.AppConfig, filePath string, fileName string) (string, error) {
	log.Printf("[STORAGE] Iniciando subida de %s a DO Spaces...", fileName)

	// 1. Configurar credenciales estáticas
	creds := credentials.NewStaticCredentialsProvider(appCfg.DOSpacesKey, appCfg.DOSpacesSecret, "")

	// 2. Cargar configuración de AWS adaptada
	cfg, err := awsconfig.LoadDefaultConfig(ctx,
		awsconfig.WithRegion(appCfg.DOSpacesRegion),
		awsconfig.WithCredentialsProvider(creds),
	)
	if err != nil {
		return "", fmt.Errorf("error cargando configuración AWS: %w", err)
	}

	// 3. Crear el cliente de S3 forzando el endpoint de DO Spaces
	client := s3.NewFromConfig(cfg, func(o *s3.Options) {
		o.BaseEndpoint = aws.String(appCfg.DOSpacesEndpoint)
	})

	// 4. Abrir el archivo físico COG recién creado
	file, err := os.Open(filePath)
	if err != nil {
		return "", fmt.Errorf("error abriendo archivo %s: %w", filePath, err)
	}
	defer file.Close()

	// 5. Construir la ruta de destino (Object Key)
	// Lo guardaremos en una subcarpeta llamada "mapas" dentro de tu Space
	objectKey := fmt.Sprintf("mapas/%s", fileName)

	// 6. Ejecutar la subida
	_, err = client.PutObject(ctx, &s3.PutObjectInput{
		Bucket:      aws.String(appCfg.DOSpacesBucket),
		Key:         aws.String(objectKey),
		Body:        file,
		ACL:         types.ObjectCannedACLPublicRead, // ¡CRÍTICO! Hace que el archivo sea público para React
		ContentType: aws.String("image/tiff"),
	})

	if err != nil {
		return "", fmt.Errorf("error subiendo objeto a Spaces: %w", err)
	}

	// 7. Construir y retornar la URL pública resultante
	// DigitalOcean estructura sus URLs públicas de esta manera:
	publicURL := fmt.Sprintf("https://%s.%s.cdn.digitaloceanspaces.com/%s",
		appCfg.DOSpacesBucket,
		appCfg.DOSpacesRegion,
		objectKey,
	)

	log.Printf("[STORAGE] Subida exitosa. URL: %s", publicURL)
	return publicURL, nil
}
