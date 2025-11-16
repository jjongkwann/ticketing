package config

import (
	"fmt"
	"os"
	"strconv"
)

type Config struct {
	// AWS
	AWSRegion string

	// DynamoDB
	SeatsTable        string
	ReservationsTable string
	BookingsTable     string

	// Redis
	RedisEndpoint string
	RedisDB       int
	RedisLockTTL  int // seconds

	// Server
	GRPCPort string
	HTTPPort string

	// Reservation
	ReservationTTLMinutes           int
	ReservationCleanupIntervalSec   int

	// Logging
	LogLevel string

	// Environment
	Environment string
}

func Load() (*Config, error) {
	redisDB, err := strconv.Atoi(getEnv("REDIS_DB", "0"))
	if err != nil {
		return nil, fmt.Errorf("invalid REDIS_DB: %w", err)
	}

	redisLockTTL, err := strconv.Atoi(getEnv("REDIS_LOCK_TTL", "30"))
	if err != nil {
		return nil, fmt.Errorf("invalid REDIS_LOCK_TTL: %w", err)
	}

	reservationTTL, err := strconv.Atoi(getEnv("RESERVATION_TTL_MINUTES", "10"))
	if err != nil {
		return nil, fmt.Errorf("invalid RESERVATION_TTL_MINUTES: %w", err)
	}

	cleanupInterval, err := strconv.Atoi(getEnv("RESERVATION_CLEANUP_INTERVAL_SECONDS", "60"))
	if err != nil {
		return nil, fmt.Errorf("invalid RESERVATION_CLEANUP_INTERVAL_SECONDS: %w", err)
	}

	return &Config{
		AWSRegion:                       getEnv("AWS_REGION", "us-east-1"),
		SeatsTable:                      getEnv("DYNAMODB_SEATS_TABLE", "ticketing-seats-prod"),
		ReservationsTable:               getEnv("DYNAMODB_RESERVATIONS_TABLE", "ticketing-reservations-prod"),
		BookingsTable:                   getEnv("DYNAMODB_BOOKINGS_TABLE", "ticketing-bookings-prod"),
		RedisEndpoint:                   getEnv("REDIS_ENDPOINT", "localhost:6379"),
		RedisDB:                         redisDB,
		RedisLockTTL:                    redisLockTTL,
		GRPCPort:                        getEnv("GRPC_PORT", "50051"),
		HTTPPort:                        getEnv("HTTP_PORT", "8080"),
		ReservationTTLMinutes:           reservationTTL,
		ReservationCleanupIntervalSec:   cleanupInterval,
		LogLevel:                        getEnv("LOG_LEVEL", "info"),
		Environment:                     getEnv("ENVIRONMENT", "production"),
	}, nil
}

func getEnv(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value
}
