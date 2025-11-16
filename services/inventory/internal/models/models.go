package models

import "time"

// SeatStatus represents the status of a seat
type SeatStatus string

const (
	SeatStatusAvailable SeatStatus = "AVAILABLE"
	SeatStatusReserved  SeatStatus = "RESERVED"
	SeatStatusBooked    SeatStatus = "BOOKED"
)

// Seat represents a seat in the inventory (DynamoDB seats table)
type Seat struct {
	EventID     string     `dynamodbav:"event_id"`
	SeatNumber  string     `dynamodbav:"seat_number"`
	Status      SeatStatus `dynamodbav:"status"`
	UserID      string     `dynamodbav:"user_id,omitempty"`
	Price       float64    `dynamodbav:"price"`
	ReservedAt  int64      `dynamodbav:"reserved_at,omitempty"` // Unix timestamp
	Version     int        `dynamodbav:"version"`                // For optimistic locking
	CreatedAt   int64      `dynamodbav:"created_at"`
	UpdatedAt   int64      `dynamodbav:"updated_at"`
}

// Reservation represents a temporary seat reservation (DynamoDB reservations table)
type Reservation struct {
	ReservationID string  `dynamodbav:"reservation_id"` // PK
	EventID       string  `dynamodbav:"event_id"`       // GSI
	SeatNumber    string  `dynamodbav:"seat_number"`
	UserID        string  `dynamodbav:"user_id"` // GSI
	Price         float64 `dynamodbav:"price"`
	CreatedAt     int64   `dynamodbav:"created_at"`
	ExpiresAt     int64   `dynamodbav:"expires_at"` // TTL attribute
	Status        string  `dynamodbav:"status"`     // PENDING, CONFIRMED, CANCELLED, EXPIRED
}

// Booking represents a confirmed booking (DynamoDB bookings table)
type Booking struct {
	BookingID  string  `dynamodbav:"booking_id"`  // PK
	EventID    string  `dynamodbav:"event_id"`    // GSI
	SeatNumber string  `dynamodbav:"seat_number"`
	UserID     string  `dynamodbav:"user_id"` // GSI
	Price      float64 `dynamodbav:"price"`
	PaymentID  string  `dynamodbav:"payment_id"`
	CreatedAt  int64   `dynamodbav:"created_at"`
	Status     string  `dynamodbav:"status"` // CONFIRMED, CANCELLED
}

// NewReservation creates a new reservation with TTL
func NewReservation(reservationID, eventID, seatNumber, userID string, price float64, ttlMinutes int) *Reservation {
	now := time.Now()
	return &Reservation{
		ReservationID: reservationID,
		EventID:       eventID,
		SeatNumber:    seatNumber,
		UserID:        userID,
		Price:         price,
		CreatedAt:     now.Unix(),
		ExpiresAt:     now.Add(time.Duration(ttlMinutes) * time.Minute).Unix(),
		Status:        "PENDING",
	}
}

// IsExpired checks if a reservation has expired
func (r *Reservation) IsExpired() bool {
	return time.Now().Unix() > r.ExpiresAt
}
