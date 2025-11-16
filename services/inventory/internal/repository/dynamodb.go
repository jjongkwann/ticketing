package repository

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/feature/dynamodb/attributevalue"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb/types"
	"github.com/google/uuid"
	"github.com/ticketing/inventory/internal/config"
	"github.com/ticketing/inventory/internal/models"
)

var (
	ErrSeatNotFound       = errors.New("seat not found")
	ErrSeatAlreadyReserved = errors.New("seat already reserved")
	ErrVersionMismatch    = errors.New("version mismatch - concurrent modification detected")
	ErrReservationNotFound = errors.New("reservation not found")
)

type DynamoDBRepository struct {
	client *dynamodb.Client
	cfg    *config.Config
}

func NewDynamoDBRepository(client *dynamodb.Client, cfg *config.Config) *DynamoDBRepository {
	return &DynamoDBRepository{
		client: client,
		cfg:    cfg,
	}
}

// GetSeats retrieves seats for an event with optional status filter
func (r *DynamoDBRepository) GetSeats(ctx context.Context, eventID string, statusFilter *models.SeatStatus, limit int32) ([]*models.Seat, error) {
	input := &dynamodb.QueryInput{
		TableName:              aws.String(r.cfg.SeatsTable),
		KeyConditionExpression: aws.String("event_id = :event_id"),
		ExpressionAttributeValues: map[string]types.AttributeValue{
			":event_id": &types.AttributeValueMemberS{Value: eventID},
		},
		Limit: aws.Int32(limit),
	}

	// 상태 필터 추가
	if statusFilter != nil {
		input.FilterExpression = aws.String("#status = :status")
		input.ExpressionAttributeNames = map[string]string{
			"#status": "status",
		}
		input.ExpressionAttributeValues[":status"] = &types.AttributeValueMemberS{Value: string(*statusFilter)}
	}

	result, err := r.client.Query(ctx, input)
	if err != nil {
		return nil, fmt.Errorf("failed to query seats: %w", err)
	}

	var seats []*models.Seat
	err = attributevalue.UnmarshalListOfMaps(result.Items, &seats)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal seats: %w", err)
	}

	return seats, nil
}

// GetSeat retrieves a single seat
func (r *DynamoDBRepository) GetSeat(ctx context.Context, eventID, seatNumber string) (*models.Seat, error) {
	input := &dynamodb.GetItemInput{
		TableName: aws.String(r.cfg.SeatsTable),
		Key: map[string]types.AttributeValue{
			"event_id":    &types.AttributeValueMemberS{Value: eventID},
			"seat_number": &types.AttributeValueMemberS{Value: seatNumber},
		},
	}

	result, err := r.client.GetItem(ctx, input)
	if err != nil {
		return nil, fmt.Errorf("failed to get seat: %w", err)
	}

	if result.Item == nil {
		return nil, ErrSeatNotFound
	}

	var seat models.Seat
	err = attributevalue.UnmarshalMap(result.Item, &seat)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal seat: %w", err)
	}

	return &seat, nil
}

// ReserveSeat reserves a seat using conditional write (optimistic locking)
func (r *DynamoDBRepository) ReserveSeat(ctx context.Context, eventID, seatNumber, userID string, currentVersion int) error {
	now := time.Now().Unix()

	input := &dynamodb.UpdateItemInput{
		TableName: aws.String(r.cfg.SeatsTable),
		Key: map[string]types.AttributeValue{
			"event_id":    &types.AttributeValueMemberS{Value: eventID},
			"seat_number": &types.AttributeValueMemberS{Value: seatNumber},
		},
		// 조건: status가 AVAILABLE이고 version이 일치해야 함
		ConditionExpression: aws.String("#status = :available AND #version = :current_version"),
		UpdateExpression:    aws.String("SET #status = :reserved, user_id = :user_id, reserved_at = :reserved_at, #version = :new_version, updated_at = :updated_at"),
		ExpressionAttributeNames: map[string]string{
			"#status":  "status",
			"#version": "version",
		},
		ExpressionAttributeValues: map[string]types.AttributeValue{
			":available":      &types.AttributeValueMemberS{Value: string(models.SeatStatusAvailable)},
			":reserved":       &types.AttributeValueMemberS{Value: string(models.SeatStatusReserved)},
			":current_version": &types.AttributeValueMemberN{Value: fmt.Sprintf("%d", currentVersion)},
			":new_version":    &types.AttributeValueMemberN{Value: fmt.Sprintf("%d", currentVersion+1)},
			":user_id":        &types.AttributeValueMemberS{Value: userID},
			":reserved_at":    &types.AttributeValueMemberN{Value: fmt.Sprintf("%d", now)},
			":updated_at":     &types.AttributeValueMemberN{Value: fmt.Sprintf("%d", now)},
		},
	}

	_, err := r.client.UpdateItem(ctx, input)
	if err != nil {
		var ccf *types.ConditionalCheckFailedException
		if errors.As(err, &ccf) {
			return ErrSeatAlreadyReserved
		}
		return fmt.Errorf("failed to reserve seat: %w", err)
	}

	return nil
}

// ReleaseSeat releases a reserved seat
func (r *DynamoDBRepository) ReleaseSeat(ctx context.Context, eventID, seatNumber, userID string) error {
	now := time.Now().Unix()

	input := &dynamodb.UpdateItemInput{
		TableName: aws.String(r.cfg.SeatsTable),
		Key: map[string]types.AttributeValue{
			"event_id":    &types.AttributeValueMemberS{Value: eventID},
			"seat_number": &types.AttributeValueMemberS{Value: seatNumber},
		},
		// 조건: status가 RESERVED이고 user_id가 일치해야 함
		ConditionExpression: aws.String("#status = :reserved AND user_id = :user_id"),
		UpdateExpression:    aws.String("SET #status = :available, #version = #version + :inc, updated_at = :updated_at REMOVE user_id, reserved_at"),
		ExpressionAttributeNames: map[string]string{
			"#status":  "status",
			"#version": "version",
		},
		ExpressionAttributeValues: map[string]types.AttributeValue{
			":reserved":   &types.AttributeValueMemberS{Value: string(models.SeatStatusReserved)},
			":available":  &types.AttributeValueMemberS{Value: string(models.SeatStatusAvailable)},
			":user_id":    &types.AttributeValueMemberS{Value: userID},
			":inc":        &types.AttributeValueMemberN{Value: "1"},
			":updated_at": &types.AttributeValueMemberN{Value: fmt.Sprintf("%d", now)},
		},
	}

	_, err := r.client.UpdateItem(ctx, input)
	if err != nil {
		var ccf *types.ConditionalCheckFailedException
		if errors.As(err, &ccf) {
			return ErrVersionMismatch
		}
		return fmt.Errorf("failed to release seat: %w", err)
	}

	return nil
}

// ConfirmSeat confirms a seat booking (after payment)
func (r *DynamoDBRepository) ConfirmSeat(ctx context.Context, eventID, seatNumber, userID string) error {
	now := time.Now().Unix()

	input := &dynamodb.UpdateItemInput{
		TableName: aws.String(r.cfg.SeatsTable),
		Key: map[string]types.AttributeValue{
			"event_id":    &types.AttributeValueMemberS{Value: eventID},
			"seat_number": &types.AttributeValueMemberS{Value: seatNumber},
		},
		ConditionExpression: aws.String("#status = :reserved AND user_id = :user_id"),
		UpdateExpression:    aws.String("SET #status = :booked, #version = #version + :inc, updated_at = :updated_at"),
		ExpressionAttributeNames: map[string]string{
			"#status":  "status",
			"#version": "version",
		},
		ExpressionAttributeValues: map[string]types.AttributeValue{
			":reserved":   &types.AttributeValueMemberS{Value: string(models.SeatStatusReserved)},
			":booked":     &types.AttributeValueMemberS{Value: string(models.SeatStatusBooked)},
			":user_id":    &types.AttributeValueMemberS{Value: userID},
			":inc":        &types.AttributeValueMemberN{Value: "1"},
			":updated_at": &types.AttributeValueMemberN{Value: fmt.Sprintf("%d", now)},
		},
	}

	_, err := r.client.UpdateItem(ctx, input)
	if err != nil {
		return fmt.Errorf("failed to confirm seat: %w", err)
	}

	return nil
}

// CreateReservation creates a reservation record
func (r *DynamoDBRepository) CreateReservation(ctx context.Context, reservation *models.Reservation) error {
	item, err := attributevalue.MarshalMap(reservation)
	if err != nil {
		return fmt.Errorf("failed to marshal reservation: %w", err)
	}

	input := &dynamodb.PutItemInput{
		TableName: aws.String(r.cfg.ReservationsTable),
		Item:      item,
	}

	_, err = r.client.PutItem(ctx, input)
	if err != nil {
		return fmt.Errorf("failed to create reservation: %w", err)
	}

	return nil
}

// GetReservation retrieves a reservation by ID
func (r *DynamoDBRepository) GetReservation(ctx context.Context, reservationID string) (*models.Reservation, error) {
	input := &dynamodb.GetItemInput{
		TableName: aws.String(r.cfg.ReservationsTable),
		Key: map[string]types.AttributeValue{
			"reservation_id": &types.AttributeValueMemberS{Value: reservationID},
		},
	}

	result, err := r.client.GetItem(ctx, input)
	if err != nil {
		return nil, fmt.Errorf("failed to get reservation: %w", err)
	}

	if result.Item == nil {
		return nil, ErrReservationNotFound
	}

	var reservation models.Reservation
	err = attributevalue.UnmarshalMap(result.Item, &reservation)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal reservation: %w", err)
	}

	return &reservation, nil
}

// UpdateReservationStatus updates reservation status
func (r *DynamoDBRepository) UpdateReservationStatus(ctx context.Context, reservationID, status string) error {
	input := &dynamodb.UpdateItemInput{
		TableName: aws.String(r.cfg.ReservationsTable),
		Key: map[string]types.AttributeValue{
			"reservation_id": &types.AttributeValueMemberS{Value: reservationID},
		},
		UpdateExpression: aws.String("SET #status = :status"),
		ExpressionAttributeNames: map[string]string{
			"#status": "status",
		},
		ExpressionAttributeValues: map[string]types.AttributeValue{
			":status": &types.AttributeValueMemberS{Value: status},
		},
	}

	_, err := r.client.UpdateItem(ctx, input)
	if err != nil {
		return fmt.Errorf("failed to update reservation status: %w", err)
	}

	return nil
}

// CreateBooking creates a confirmed booking
func (r *DynamoDBRepository) CreateBooking(ctx context.Context, reservation *models.Reservation, paymentID string) (string, error) {
	bookingID := uuid.New().String()

	booking := &models.Booking{
		BookingID:  bookingID,
		EventID:    reservation.EventID,
		SeatNumber: reservation.SeatNumber,
		UserID:     reservation.UserID,
		Price:      reservation.Price,
		PaymentID:  paymentID,
		CreatedAt:  time.Now().Unix(),
		Status:     "CONFIRMED",
	}

	item, err := attributevalue.MarshalMap(booking)
	if err != nil {
		return "", fmt.Errorf("failed to marshal booking: %w", err)
	}

	input := &dynamodb.PutItemInput{
		TableName: aws.String(r.cfg.BookingsTable),
		Item:      item,
	}

	_, err = r.client.PutItem(ctx, input)
	if err != nil {
		return "", fmt.Errorf("failed to create booking: %w", err)
	}

	return bookingID, nil
}

// InitializeSeats creates initial seats for an event
func (r *DynamoDBRepository) InitializeSeats(ctx context.Context, eventID string, totalSeats int, price float64) (int, error) {
	now := time.Now().Unix()
	created := 0

	// 배치로 처리 (25개씩)
	batchSize := 25
	for i := 0; i < totalSeats; i += batchSize {
		end := i + batchSize
		if end > totalSeats {
			end = totalSeats
		}

		var writeRequests []types.WriteRequest
		for j := i; j < end; j++ {
			seatNumber := fmt.Sprintf("S-%04d", j+1)
			seat := &models.Seat{
				EventID:    eventID,
				SeatNumber: seatNumber,
				Status:     models.SeatStatusAvailable,
				Price:      price,
				Version:    0,
				CreatedAt:  now,
				UpdatedAt:  now,
			}

			item, err := attributevalue.MarshalMap(seat)
			if err != nil {
				return created, fmt.Errorf("failed to marshal seat: %w", err)
			}

			writeRequests = append(writeRequests, types.WriteRequest{
				PutRequest: &types.PutRequest{
					Item: item,
				},
			})
		}

		input := &dynamodb.BatchWriteItemInput{
			RequestItems: map[string][]types.WriteRequest{
				r.cfg.SeatsTable: writeRequests,
			},
		}

		_, err := r.client.BatchWriteItem(ctx, input)
		if err != nil {
			return created, fmt.Errorf("failed to batch write seats: %w", err)
		}

		created += len(writeRequests)
	}

	return created, nil
}
