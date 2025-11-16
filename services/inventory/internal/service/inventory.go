package service

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/google/uuid"
	"github.com/ticketing/inventory/internal/config"
	"github.com/ticketing/inventory/internal/models"
	"github.com/ticketing/inventory/internal/repository"
)

type InventoryService struct {
	dynamoDB *repository.DynamoDBRepository
	redis    *repository.RedisRepository
	cfg      *config.Config
}

func NewInventoryService(
	dynamoDB *repository.DynamoDBRepository,
	redis *repository.RedisRepository,
	cfg *config.Config,
) *InventoryService {
	return &InventoryService{
		dynamoDB: dynamoDB,
		redis:    redis,
		cfg:      cfg,
	}
}

// GetSeats retrieves available seats for an event
func (s *InventoryService) GetSeats(ctx context.Context, eventID string, statusFilter *models.SeatStatus, limit int32) ([]*models.Seat, error) {
	return s.dynamoDB.GetSeats(ctx, eventID, statusFilter, limit)
}

// ReserveSeat reserves a seat with distributed locking
func (s *InventoryService) ReserveSeat(ctx context.Context, eventID, seatNumber, userID string) (string, error) {
	// Step 1: Acquire distributed lock (Redis)
	lockToken, err := s.redis.AcquireLock(ctx, eventID, seatNumber)
	if err != nil {
		return "", fmt.Errorf("failed to acquire lock: %w", err)
	}

	// Ensure lock is released
	defer func() {
		if releaseErr := s.redis.ReleaseLock(context.Background(), eventID, seatNumber, lockToken); releaseErr != nil {
			log.Printf("Warning: failed to release lock for %s/%s: %v", eventID, seatNumber, releaseErr)
		}
	}()

	// Step 2: Get seat to check current state and version
	seat, err := s.dynamoDB.GetSeat(ctx, eventID, seatNumber)
	if err != nil {
		return "", fmt.Errorf("failed to get seat: %w", err)
	}

	if seat.Status != models.SeatStatusAvailable {
		return "", repository.ErrSeatAlreadyReserved
	}

	// Step 3: Reserve seat in DynamoDB with conditional write
	err = s.dynamoDB.ReserveSeat(ctx, eventID, seatNumber, userID, seat.Version)
	if err != nil {
		return "", fmt.Errorf("failed to reserve seat in dynamodb: %w", err)
	}

	// Step 4: Create reservation record
	reservationID := uuid.New().String()
	reservation := models.NewReservation(
		reservationID,
		eventID,
		seatNumber,
		userID,
		seat.Price,
		s.cfg.ReservationTTLMinutes,
	)

	err = s.dynamoDB.CreateReservation(ctx, reservation)
	if err != nil {
		// Rollback: release seat
		rollbackErr := s.dynamoDB.ReleaseSeat(context.Background(), eventID, seatNumber, userID)
		if rollbackErr != nil {
			log.Printf("Critical: failed to rollback seat reservation: %v", rollbackErr)
		}
		return "", fmt.Errorf("failed to create reservation: %w", err)
	}

	return reservationID, nil
}

// ReleaseSeat releases a reserved seat
func (s *InventoryService) ReleaseSeat(ctx context.Context, eventID, seatNumber, userID string) error {
	// Acquire lock
	lockToken, err := s.redis.AcquireLock(ctx, eventID, seatNumber)
	if err != nil {
		return fmt.Errorf("failed to acquire lock: %w", err)
	}

	defer func() {
		if releaseErr := s.redis.ReleaseLock(context.Background(), eventID, seatNumber, lockToken); releaseErr != nil {
			log.Printf("Warning: failed to release lock: %v", releaseErr)
		}
	}()

	// Release seat in DynamoDB
	err = s.dynamoDB.ReleaseSeat(ctx, eventID, seatNumber, userID)
	if err != nil {
		return fmt.Errorf("failed to release seat: %w", err)
	}

	return nil
}

// ConfirmBooking confirms a booking after payment success
func (s *InventoryService) ConfirmBooking(ctx context.Context, reservationID, userID, paymentID string) (string, error) {
	// Get reservation
	reservation, err := s.dynamoDB.GetReservation(ctx, reservationID)
	if err != nil {
		return "", fmt.Errorf("failed to get reservation: %w", err)
	}

	// Check if reservation is expired
	if reservation.IsExpired() {
		return "", fmt.Errorf("reservation has expired")
	}

	// Check user ownership
	if reservation.UserID != userID {
		return "", fmt.Errorf("reservation does not belong to user")
	}

	// Acquire lock
	lockToken, err := s.redis.AcquireLock(ctx, reservation.EventID, reservation.SeatNumber)
	if err != nil {
		return "", fmt.Errorf("failed to acquire lock: %w", err)
	}

	defer func() {
		if releaseErr := s.redis.ReleaseLock(context.Background(), reservation.EventID, reservation.SeatNumber, lockToken); releaseErr != nil {
			log.Printf("Warning: failed to release lock: %v", releaseErr)
		}
	}()

	// Confirm seat booking
	err = s.dynamoDB.ConfirmSeat(ctx, reservation.EventID, reservation.SeatNumber, userID)
	if err != nil {
		return "", fmt.Errorf("failed to confirm seat: %w", err)
	}

	// Create booking record
	bookingID, err := s.dynamoDB.CreateBooking(ctx, reservation, paymentID)
	if err != nil {
		return "", fmt.Errorf("failed to create booking: %w", err)
	}

	// Update reservation status
	err = s.dynamoDB.UpdateReservationStatus(ctx, reservationID, "CONFIRMED")
	if err != nil {
		log.Printf("Warning: failed to update reservation status: %v", err)
	}

	return bookingID, nil
}

// InitializeSeats initializes seats for an event
func (s *InventoryService) InitializeSeats(ctx context.Context, eventID string, totalSeats int, price float64) (int, error) {
	return s.dynamoDB.InitializeSeats(ctx, eventID, totalSeats, price)
}

// CleanupExpiredReservations runs as a background goroutine to clean up expired reservations
func (s *InventoryService) CleanupExpiredReservations(ctx context.Context) {
	ticker := time.NewTicker(time.Duration(s.cfg.ReservationCleanupIntervalSec) * time.Second)
	defer ticker.Stop()

	log.Println("Starting reservation cleanup goroutine...")

	for {
		select {
		case <-ctx.Done():
			log.Println("Stopping reservation cleanup goroutine")
			return
		case <-ticker.C:
			// TODO: Implement cleanup logic
			// 1. Query reservations table with TTL expired
			// 2. Release corresponding seats in seats table
			log.Println("Running reservation cleanup...")
		}
	}
}
