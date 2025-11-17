package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	awsconfig "github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb"
	"github.com/go-redis/redis/v8"
	"github.com/ticketing/inventory/internal/config"
	grpcServer "github.com/ticketing/inventory/internal/grpc"
	httpServer "github.com/ticketing/inventory/internal/http"
	"github.com/ticketing/inventory/internal/repository"
	"github.com/ticketing/inventory/internal/service"
)

func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	// Initialize AWS config
	awsCfg, err := awsconfig.LoadDefaultConfig(context.Background(),
		awsconfig.WithRegion(cfg.AWSRegion),
	)
	if err != nil {
		log.Fatalf("Failed to load AWS config: %v", err)
	}

	// Initialize DynamoDB client
	dynamoClient := dynamodb.NewFromConfig(awsCfg, func(o *dynamodb.Options) {
		if endpoint := os.Getenv("DYNAMODB_ENDPOINT"); endpoint != "" {
			o.BaseEndpoint = aws.String(endpoint)
		}
	})

	// Initialize Redis client
	redisClient := redis.NewClient(&redis.Options{
		Addr:     cfg.RedisEndpoint,
		Password: os.Getenv("REDIS_PASSWORD"),
		DB:       cfg.RedisDB,
	})

	// Test Redis connection
	ctx := context.Background()
	if err := redisClient.Ping(ctx).Err(); err != nil {
		log.Fatalf("Failed to connect to Redis: %v", err)
	}

	// Initialize repositories
	dynamoRepo := repository.NewDynamoDBRepository(dynamoClient, cfg)
	redisRepo := repository.NewRedisRepository(redisClient, cfg)

	// Initialize service
	invService := service.NewInventoryService(dynamoRepo, redisRepo, cfg)

	// Start cleanup goroutine
	cleanupCtx, cleanupCancel := context.WithCancel(context.Background())
	defer cleanupCancel()
	go invService.CleanupExpiredReservations(cleanupCtx)

	// Initialize servers
	grpcSrv := grpcServer.NewGRPCServer(invService, cfg)
	httpSrv := httpServer.NewHTTPServer(cfg)

	// Start servers in goroutines
	errChan := make(chan error, 2)

	go func() {
		if err := grpcSrv.Start(); err != nil {
			errChan <- err
		}
	}()

	go func() {
		if err := httpSrv.Start(); err != nil {
			errChan <- err
		}
	}()

	// Wait for interrupt signal
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	select {
	case err := <-errChan:
		log.Fatalf("Server error: %v", err)
	case sig := <-sigChan:
		log.Printf("Received signal: %v, shutting down...", sig)
		cleanupCancel()

		shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()

		if err := httpSrv.Shutdown(shutdownCtx); err != nil {
			log.Printf("Error shutting down HTTP server: %v", err)
		}

		log.Println("Server shutdown complete")
	}
}
