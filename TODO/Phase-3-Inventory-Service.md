# Phase 3: Inventory Service (Go) - Core Concurrency Control

## 📋 Overview
This is the **MOST CRITICAL PHASE** of the entire system. The Inventory Service, written in Go, implements distributed locking with Redis to prevent race conditions and ensure zero double-booking. This service manages the seat state machine, reservation creation with TTL, and reservation expiry cleanup.

## 🎯 Objectives
- Implement high-performance Inventory Service in Go
- Implement distributed locking with Redis (Redlock or simple SETNX)
- Implement optimistic locking with version numbers
- Create reservation system with automatic expiry (TTL)
- Build scheduled cleanup job for expired reservations
- Achieve <500ms seat availability check, <2s reservation creation

## 👥 Agents Involved
- **golang-pro**: Go service implementation with concurrency expertise

---

## 📝 Tasks

### T3.1: Implement Inventory Service in Go with Distributed Locking
**Agent**: `golang-pro`
**Dependencies**: T1.2 (Docker), T1.3 (DB schemas)
**Status**: ⏳ Pending
**Parallel**: No

**Description**:
Implement a Go-based REST API service that manages seat availability, reservations, and implements distributed locking with Redis to prevent race conditions.

**Technology Stack**:
- Go 1.21+
- Gin (HTTP framework)
- GORM (ORM for MySQL)
- go-redis/redis (Redis client)
- Redlock or custom Redis locking

**Expected Output**:

**Project Structure**:
```
services/inventory/
├── cmd/
│   └── server/
│       └── main.go
├── internal/
│   ├── config/
│   │   └── config.go
│   ├── models/
│   │   ├── seat.go
│   │   └── reservation.go
│   ├── repository/
│   │   ├── seat_repository.go
│   │   └── reservation_repository.go
│   ├── service/
│   │   ├── inventory_service.go
│   │   └── lock_service.go
│   ├── handler/
│   │   ├── seat_handler.go
│   │   └── reservation_handler.go
│   └── middleware/
│       └── auth.go
├── pkg/
│   ├── redlock/
│   │   └── redlock.go
│   └── errors/
│       └── errors.go
├── go.mod
├── go.sum
├── Dockerfile
└── README.md
```

**Core Models** (`internal/models/`):

```go
// seat.go
package models

import "time"

type SeatStatus string

const (
    SeatAvailable SeatStatus = "AVAILABLE"
    SeatReserved  SeatStatus = "RESERVED"
    SeatBooked    SeatStatus = "BOOKED"
    SeatBlocked   SeatStatus = "BLOCKED"
)

type SeatType string

const (
    SeatRegular SeatType = "REGULAR"
    SeatVIP     SeatType = "VIP"
    SeatPremium SeatType = "PREMIUM"
)

type Seat struct {
    SeatID        int64      `gorm:"primaryKey;autoIncrement" json:"seatId"`
    EventID       int64      `gorm:"not null;index:idx_event_status" json:"eventId"`
    SeatNumber    string     `gorm:"size:20;not null" json:"seatNumber"`
    Section       string     `gorm:"size:50" json:"section"`
    RowNumber     string     `gorm:"size:10" json:"rowNumber"`
    SeatType      SeatType   `gorm:"type:ENUM('REGULAR','VIP','PREMIUM');default:'REGULAR'" json:"seatType"`
    Price         float64    `gorm:"type:decimal(10,2);not null" json:"price"`
    Status        SeatStatus `gorm:"type:ENUM('AVAILABLE','RESERVED','BOOKED','BLOCKED');default:'AVAILABLE';index:idx_event_status" json:"status"`
    Version       int64      `gorm:"default:0;index" json:"version"`  // For optimistic locking
    ReservedBy    *string    `gorm:"size:50" json:"reservedBy,omitempty"`
    ReservedUntil *time.Time `gorm:"index:idx_reserved_until" json:"reservedUntil,omitempty"`
    BookingID     *int64     `json:"bookingId,omitempty"`
    CreatedAt     time.Time  `gorm:"autoCreateTime" json:"createdAt"`
}

// reservation.go
type ReservationStatus string

const (
    ReservationActive    ReservationStatus = "ACTIVE"
    ReservationConfirmed ReservationStatus = "CONFIRMED"
    ReservationExpired   ReservationStatus = "EXPIRED"
    ReservationCancelled ReservationStatus = "CANCELLED"
)

type Reservation struct {
    ReservationID int64             `gorm:"primaryKey;autoIncrement" json:"reservationId"`
    SeatID        int64             `gorm:"not null;index:idx_seat_id" json:"seatId"`
    EventID       int64             `gorm:"not null" json:"eventId"`
    UserID        string            `gorm:"size:50;not null;index:idx_user_id" json:"userId"`
    SessionID     *string           `gorm:"size:100" json:"sessionId,omitempty"`
    ExpiresAt     time.Time         `gorm:"not null;index:idx_expires_at" json:"expiresAt"`
    Status        ReservationStatus `gorm:"type:ENUM('ACTIVE','CONFIRMED','EXPIRED','CANCELLED');default:'ACTIVE';index" json:"status"`
    CreatedAt     time.Time         `gorm:"autoCreateTime" json:"createdAt"`
}
```

**Redis Distributed Lock** (`pkg/redlock/redlock.go`):

```go
package redlock

import (
    "context"
    "crypto/rand"
    "encoding/base64"
    "errors"
    "time"

    "github.com/go-redis/redis/v8"
)

const (
    DefaultLockTTL = 30 * time.Second
    ClockDriftFactor = 0.01
)

type RedisLock struct {
    client *redis.Client
}

func NewRedisLock(client *redis.Client) *RedisLock {
    return &RedisLock{client: client}
}

// AcquireLock attempts to acquire a distributed lock
func (rl *RedisLock) AcquireLock(ctx context.Context, resource string, ttl time.Duration) (string, error) {
    // Generate unique lock value
    lockValue := generateLockValue()

    // Try to acquire lock with SETNX
    success, err := rl.client.SetNX(ctx, lockKey(resource), lockValue, ttl).Result()
    if err != nil {
        return "", err
    }

    if !success {
        return "", errors.New("failed to acquire lock: already held")
    }

    return lockValue, nil
}

// ReleaseLock releases the lock only if the value matches (Lua script for atomicity)
func (rl *RedisLock) ReleaseLock(ctx context.Context, resource string, lockValue string) error {
    luaScript := `
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
    `

    _, err := rl.client.Eval(ctx, luaScript, []string{lockKey(resource)}, lockValue).Result()
    return err
}

func lockKey(resource string) string {
    return "lock:" + resource
}

func generateLockValue() string {
    b := make([]byte, 16)
    rand.Read(b)
    return base64.URLEncoding.EncodeToString(b)
}
```

**Inventory Service** (`internal/service/inventory_service.go`):

```go
package service

import (
    "context"
    "errors"
    "fmt"
    "time"

    "inventory-service/internal/models"
    "inventory-service/internal/repository"
    "inventory-service/pkg/redlock"
)

const (
    ReservationTTL = 10 * time.Minute
    LockTimeout    = 30 * time.Second
)

type InventoryService struct {
    seatRepo        repository.SeatRepository
    reservationRepo repository.ReservationRepository
    redisLock       *redlock.RedisLock
}

func NewInventoryService(
    seatRepo repository.SeatRepository,
    reservationRepo repository.ReservationRepository,
    redisLock *redlock.RedisLock,
) *InventoryService {
    return &InventoryService{
        seatRepo:        seatRepo,
        reservationRepo: reservationRepo,
        redisLock:       redisLock,
    }
}

// GetAvailableSeats returns all available seats for an event
func (s *InventoryService) GetAvailableSeats(ctx context.Context, eventID int64) ([]models.Seat, error) {
    return s.seatRepo.FindByEventAndStatus(ctx, eventID, models.SeatAvailable)
}

// ReserveSeats reserves multiple seats with distributed locking
func (s *InventoryService) ReserveSeats(ctx context.Context, eventID int64, seatNumbers []string, userID string) ([]*models.Reservation, error) {
    // Sort seat numbers to prevent deadlock
    sort.Strings(seatNumbers)

    // Acquire locks for all seats
    lockKeys := make([]string, len(seatNumbers))
    lockValues := make([]string, len(seatNumbers))

    for i, seatNumber := range seatNumbers {
        resource := fmt.Sprintf("seat:%d:%s", eventID, seatNumber)
        lockValue, err := s.redisLock.AcquireLock(ctx, resource, LockTimeout)
        if err != nil {
            // Release any locks we acquired
            s.releaseLocks(ctx, lockKeys[:i], lockValues[:i])
            return nil, fmt.Errorf("failed to acquire lock for seat %s: %w", seatNumber, err)
        }
        lockKeys[i] = resource
        lockValues[i] = lockValue
    }

    // Ensure locks are released
    defer s.releaseLocks(ctx, lockKeys, lockValues)

    // Reserve seats
    reservations := make([]*models.Reservation, 0, len(seatNumbers))
    reservedUntil := time.Now().Add(ReservationTTL)

    for _, seatNumber := range seatNumbers {
        // Find seat
        seat, err := s.seatRepo.FindByEventAndSeatNumber(ctx, eventID, seatNumber)
        if err != nil {
            return nil, fmt.Errorf("seat not found: %s", seatNumber)
        }

        // Check availability
        if seat.Status != models.SeatAvailable {
            return nil, fmt.Errorf("seat %s is not available", seatNumber)
        }

        // Update seat status with optimistic locking
        err = s.seatRepo.UpdateStatusWithVersion(ctx, seat.SeatID, seat.Version, models.SeatReserved, &userID, &reservedUntil)
        if err != nil {
            return nil, fmt.Errorf("failed to reserve seat %s (concurrent modification)", seatNumber)
        }

        // Create reservation
        reservation := &models.Reservation{
            SeatID:    seat.SeatID,
            EventID:   eventID,
            UserID:    userID,
            ExpiresAt: reservedUntil,
            Status:    models.ReservationActive,
        }

        err = s.reservationRepo.Create(ctx, reservation)
        if err != nil {
            return nil, fmt.Errorf("failed to create reservation: %w", err)
        }

        reservations = append(reservations, reservation)
    }

    return reservations, nil
}

func (s *InventoryService) releaseLocks(ctx context.Context, lockKeys []string, lockValues []string) {
    for i, lockKey := range lockKeys {
        s.redisLock.ReleaseLock(ctx, lockKey, lockValues[i])
    }
}
```

**Repository with Optimistic Locking** (`internal/repository/seat_repository.go`):

```go
package repository

import (
    "context"
    "time"

    "gorm.io/gorm"
    "inventory-service/internal/models"
)

type SeatRepository interface {
    FindByEventAndStatus(ctx context.Context, eventID int64, status models.SeatStatus) ([]models.Seat, error)
    FindByEventAndSeatNumber(ctx context.Context, eventID int64, seatNumber string) (*models.Seat, error)
    UpdateStatusWithVersion(ctx context.Context, seatID int64, expectedVersion int64, newStatus models.SeatStatus, reservedBy *string, reservedUntil *time.Time) error
}

type seatRepository struct {
    db *gorm.DB
}

func NewSeatRepository(db *gorm.DB) SeatRepository {
    return &seatRepository{db: db}
}

func (r *seatRepository) FindByEventAndStatus(ctx context.Context, eventID int64, status models.SeatStatus) ([]models.Seat, error) {
    var seats []models.Seat
    err := r.db.WithContext(ctx).
        Where("event_id = ? AND status = ?", eventID, status).
        Find(&seats).Error
    return seats, err
}

func (r *seatRepository) FindByEventAndSeatNumber(ctx context.Context, eventID int64, seatNumber string) (*models.Seat, error) {
    var seat models.Seat
    err := r.db.WithContext(ctx).
        Where("event_id = ? AND seat_number = ?", eventID, seatNumber).
        First(&seat).Error
    return &seat, err
}

// UpdateStatusWithVersion implements optimistic locking
func (r *seatRepository) UpdateStatusWithVersion(
    ctx context.Context,
    seatID int64,
    expectedVersion int64,
    newStatus models.SeatStatus,
    reservedBy *string,
    reservedUntil *time.Time,
) error {
    result := r.db.WithContext(ctx).
        Model(&models.Seat{}).
        Where("seat_id = ? AND version = ? AND status = ?", seatID, expectedVersion, models.SeatAvailable).
        Updates(map[string]interface{}{
            "status":         newStatus,
            "reserved_by":    reservedBy,
            "reserved_until": reservedUntil,
            "version":        expectedVersion + 1,
        })

    if result.Error != nil {
        return result.Error
    }

    if result.RowsAffected == 0 {
        return errors.New("version mismatch or seat not available (concurrent modification)")
    }

    return nil
}
```

**REST API Handlers** (`internal/handler/`):

```go
// seat_handler.go
package handler

import (
    "net/http"
    "strconv"

    "github.com/gin-gonic/gin"
    "inventory-service/internal/service"
)

type SeatHandler struct {
    inventoryService *service.InventoryService
}

func NewSeatHandler(inventoryService *service.InventoryService) *SeatHandler {
    return &SeatHandler{inventoryService: inventoryService}
}

// GET /api/inventory/events/:eventId/seats/available
func (h *SeatHandler) GetAvailableSeats(c *gin.Context) {
    eventID, err := strconv.ParseInt(c.Param("eventId"), 10, 64)
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": "invalid event ID"})
        return
    }

    seats, err := h.inventoryService.GetAvailableSeats(c.Request.Context(), eventID)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }

    c.JSON(http.StatusOK, gin.H{"seats": seats})
}

// POST /api/inventory/reservations
func (h *SeatHandler) CreateReservation(c *gin.Context) {
    var req struct {
        EventID     int64    `json:"eventId" binding:"required"`
        SeatNumbers []string `json:"seatNumbers" binding:"required,min=1,max=10"`
    }

    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    // Get user ID from JWT (set by auth middleware)
    userID := c.GetString("userId")
    if userID == "" {
        c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
        return
    }

    reservations, err := h.inventoryService.ReserveSeats(
        c.Request.Context(),
        req.EventID,
        req.SeatNumbers,
        userID,
    )

    if err != nil {
        c.JSON(http.StatusConflict, gin.H{"error": err.Error()})
        return
    }

    c.JSON(http.StatusCreated, gin.H{
        "reservations": reservations,
        "expiresAt":    reservations[0].ExpiresAt,
    })
}
```

**Success Criteria**:
- [ ] Seats can be queried by event and availability
- [ ] Reservations use distributed locks (Redis)
- [ ] Optimistic locking prevents concurrent updates
- [ ] Multiple seats can be reserved atomically
- [ ] Lock acquisition errors are handled gracefully
- [ ] Latency: <500ms for seat availability, <2s for reservation
- [ ] Concurrent requests don't cause double-booking

---

### T3.2: Implement Scheduled Cleanup Job for Expired Reservations
**Agent**: `golang-pro`
**Dependencies**: T3.1
**Status**: ⏳ Pending
**Parallel**: No

**Description**:
Implement a background goroutine that periodically checks for expired reservations and releases seats back to AVAILABLE status.

**Expected Output**:

**Cleanup Service** (`internal/service/cleanup_service.go`):

```go
package service

import (
    "context"
    "log"
    "time"

    "inventory-service/internal/models"
    "inventory-service/internal/repository"
    "inventory-service/pkg/redlock"
)

type CleanupService struct {
    seatRepo        repository.SeatRepository
    reservationRepo repository.ReservationRepository
    redisLock       *redlock.RedisLock
}

func NewCleanupService(
    seatRepo repository.SeatRepository,
    reservationRepo repository.ReservationRepository,
    redisLock *redlock.RedisLock,
) *CleanupService {
    return &CleanupService{
        seatRepo:        seatRepo,
        reservationRepo: reservationRepo,
        redisLock:       redisLock,
    }
}

// StartCleanupJob starts a goroutine that runs cleanup every minute
func (s *CleanupService) StartCleanupJob(ctx context.Context) {
    ticker := time.NewTicker(1 * time.Minute)
    defer ticker.Stop()

    log.Println("Starting reservation cleanup job...")

    for {
        select {
        case <-ticker.C:
            s.cleanupExpiredReservations(ctx)
        case <-ctx.Done():
            log.Println("Stopping cleanup job...")
            return
        }
    }
}

func (s *CleanupService) cleanupExpiredReservations(ctx context.Context) {
    // Find expired reservations
    expiredReservations, err := s.reservationRepo.FindExpired(ctx, time.Now())
    if err != nil {
        log.Printf("Error finding expired reservations: %v", err)
        return
    }

    log.Printf("Found %d expired reservations to clean up", len(expiredReservations))

    for _, reservation := range expiredReservations {
        if err := s.releaseExpiredReservation(ctx, reservation); err != nil {
            log.Printf("Failed to release reservation %d: %v", reservation.ReservationID, err)
        }
    }
}

func (s *CleanupService) releaseExpiredReservation(ctx context.Context, reservation *models.Reservation) error {
    // Get seat info
    seat, err := s.seatRepo.FindByID(ctx, reservation.SeatID)
    if err != nil {
        return err
    }

    // Try to acquire lock (may fail if someone is booking concurrently)
    resource := fmt.Sprintf("seat:%d:%s", seat.EventID, seat.SeatNumber)
    lockValue, err := s.redisLock.AcquireLock(ctx, resource, 5*time.Second)
    if err != nil {
        // Lock held by someone else, skip
        return nil
    }

    defer s.redisLock.ReleaseLock(ctx, resource, lockValue)

    // Double-check seat is still reserved and expired
    if seat.Status != models.SeatReserved {
        return nil // Already released or booked
    }

    if seat.ReservedUntil == nil || time.Now().Before(*seat.ReservedUntil) {
        return nil // Not expired yet
    }

    // Release seat
    err = s.seatRepo.UpdateToAvailable(ctx, seat.SeatID)
    if err != nil {
        return err
    }

    // Mark reservation as expired
    err = s.reservationRepo.UpdateStatus(ctx, reservation.ReservationID, models.ReservationExpired)
    if err != nil {
        return err
    }

    log.Printf("Released seat %s for event %d (reservation %d)", seat.SeatNumber, seat.EventID, reservation.ReservationID)
    return nil
}
```

**Repository Methods** (add to existing repositories):

```go
// reservation_repository.go
func (r *reservationRepository) FindExpired(ctx context.Context, currentTime time.Time) ([]*models.Reservation, error) {
    var reservations []*models.Reservation
    err := r.db.WithContext(ctx).
        Where("status = ? AND expires_at < ?", models.ReservationActive, currentTime).
        Find(&reservations).Error
    return reservations, err
}

func (r *reservationRepository) UpdateStatus(ctx context.Context, reservationID int64, status models.ReservationStatus) error {
    return r.db.WithContext(ctx).
        Model(&models.Reservation{}).
        Where("reservation_id = ?", reservationID).
        Update("status", status).Error
}

// seat_repository.go
func (r *seatRepository) FindByID(ctx context.Context, seatID int64) (*models.Seat, error) {
    var seat models.Seat
    err := r.db.WithContext(ctx).First(&seat, seatID).Error
    return &seat, err
}

func (r *seatRepository) UpdateToAvailable(ctx context.Context, seatID int64) error {
    return r.db.WithContext(ctx).
        Model(&models.Seat{}).
        Where("seat_id = ?", seatID).
        Updates(map[string]interface{}{
            "status":         models.SeatAvailable,
            "reserved_by":    nil,
            "reserved_until": nil,
        }).Error
}
```

**Main Server** (`cmd/server/main.go`):

```go
package main

import (
    "context"
    "log"
    "os"
    "os/signal"
    "syscall"

    "github.com/gin-gonic/gin"
    "github.com/go-redis/redis/v8"
    "gorm.io/driver/mysql"
    "gorm.io/gorm"

    "inventory-service/internal/config"
    "inventory-service/internal/handler"
    "inventory-service/internal/repository"
    "inventory-service/internal/service"
    "inventory-service/pkg/redlock"
)

func main() {
    // Load config
    cfg := config.Load()

    // Connect to MySQL
    db, err := gorm.Open(mysql.Open(cfg.DatabaseURL), &gorm.Config{})
    if err != nil {
        log.Fatal("Failed to connect to database:", err)
    }

    // Connect to Redis
    redisClient := redis.NewClient(&redis.Options{
        Addr: cfg.RedisURL,
    })

    // Initialize dependencies
    redisLock := redlock.NewRedisLock(redisClient)
    seatRepo := repository.NewSeatRepository(db)
    reservationRepo := repository.NewReservationRepository(db)

    inventoryService := service.NewInventoryService(seatRepo, reservationRepo, redisLock)
    cleanupService := service.NewCleanupService(seatRepo, reservationRepo, redisLock)

    // Start cleanup job
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    go cleanupService.StartCleanupJob(ctx)

    // Setup HTTP server
    router := gin.Default()
    seatHandler := handler.NewSeatHandler(inventoryService)

    api := router.Group("/api/inventory")
    {
        api.GET("/events/:eventId/seats/available", seatHandler.GetAvailableSeats)
        api.POST("/reservations", seatHandler.CreateReservation)
        api.GET("/health", func(c *gin.Context) {
            c.JSON(200, gin.H{"status": "healthy"})
        })
    }

    // Graceful shutdown
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)

    go func() {
        <-quit
        log.Println("Shutting down server...")
        cancel()
    }()

    log.Println("Server starting on :8003")
    if err := router.Run(":8003"); err != nil {
        log.Fatal("Server failed:", err)
    }
}
```

**Success Criteria**:
- [ ] Cleanup job runs every minute
- [ ] Expired reservations are found and processed
- [ ] Seats are released back to AVAILABLE
- [ ] Locks are acquired during cleanup to prevent races
- [ ] Cleanup job handles errors gracefully
- [ ] Graceful shutdown stops the cleanup job

---

## 🎯 Phase 3 Success Criteria

- [ ] **Distributed Locking**: Redis locks prevent concurrent seat reservations
- [ ] **Optimistic Locking**: Version numbers prevent lost updates
- [ ] **Reservation TTL**: Reservations expire after 10 minutes
- [ ] **Cleanup Job**: Expired reservations are automatically released
- [ ] **Performance**: <500ms seat query, <2s reservation
- [ ] **Zero Double-Booking**: Load tests confirm no race conditions
- [ ] **API Documentation**: Endpoints documented

## 📊 Estimated Timeline
**4-5 days** (most critical component)

## 🔗 Dependencies
- **Previous**: [Phase 2: Auth & Events Services](./Phase-2-Auth-Events.md)
- **Next**: [Phase 4: Booking & Payment Services](./Phase-4-Booking-Payment.md)

---

## 📌 Notes
- **Redis locks are critical**: Without proper locking, double-booking WILL occur.
- **Sort seat numbers**: Always lock seats in sorted order to prevent deadlocks.
- **Optimistic locking**: Use version numbers as a second defense layer.
- **Cleanup timing**: Running every minute is a good balance; adjust if needed.
- **Lock timeout**: 30 seconds should be sufficient; monitor in production.
- **Goroutine pool**: For high load, consider limiting cleanup goroutines with a worker pool.
- **Monitoring**: Add metrics for lock acquisition time, cleanup duration, expired reservations count.
