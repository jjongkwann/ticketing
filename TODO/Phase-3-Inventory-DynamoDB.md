# Phase 3: Go Inventory Service (DynamoDB + Redis) ⭐

## 📋 Overview
**THE MOST CRITICAL SERVICE** - Implements seat inventory management with DynamoDB for storage, Redis for distributed locking, and gRPC for inter-service communication. This service ensures **zero double-booking** through multi-layer concurrency control.

## 🎯 Objectives
- Build high-performance Go service with DynamoDB SDK
- Implement distributed locking with Redis Cluster
- Use DynamoDB conditional writes for optimistic locking
- Use DynamoDB Transactions for atomic multi-seat updates
- Expose gRPC API for internal services
- Deploy to Kubernetes with HPA (5-50 pods)
- Instrument with Datadog APM
- Achieve <100ms seat query, <500ms reservation

## 👥 Agent
- **golang-pro**

---

## 📝 Implementation

### Project Structure

```
services/inventory/
├── cmd/
│   └── server/
│       └── main.go
├── internal/
│   ├── config/
│   │   └── config.go
│   ├── domain/
│   │   ├── seat.go
│   │   └── reservation.go
│   ├── repository/
│   │   ├── dynamodb/
│   │   │   ├── seat_repository.go
│   │   │   └── reservation_repository.go
│   │   └── redis/
│   │       └── lock_repository.go
│   ├── service/
│   │   ├── inventory_service.go
│   │   └── cleanup_service.go
│   ├── grpc/
│   │   ├── server.go
│   │   └── handler.go
│   └── metrics/
│       └── prometheus.go
├── api/
│   └── proto/
│       └── inventory.proto
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── hpa.yaml
├── go.mod
├── go.sum
├── Dockerfile
└── README.md
```

---

### gRPC API Definition

**`api/proto/inventory.proto`**:

```protobuf
syntax = "proto3";

package inventory.v1;

option go_package = "github.com/ticketing/inventory/api/proto";

service InventoryService {
  // Get available seats for an event
  rpc GetAvailableSeats(GetAvailableSeatsRequest) returns (GetAvailableSeatsResponse);

  // Reserve multiple seats (atomic)
  rpc ReserveSeats(ReserveSeatsRequest) returns (ReserveSeatsResponse);

  // Get reservation details
  rpc GetReservation(GetReservationRequest) returns (GetReservationResponse);

  // Confirm reservations (called by Booking Service)
  rpc ConfirmReservations(ConfirmReservationsRequest) returns (ConfirmReservationsResponse);

  // Cancel reservations
  rpc CancelReservations(CancelReservationsRequest) returns (CancelReservationsResponse);

  // Health check
  rpc HealthCheck(HealthCheckRequest) returns (HealthCheckResponse);
}

message Seat {
  int64 event_id = 1;
  string seat_number = 2;
  string section = 3;
  string row_number = 4;
  string seat_type = 5;
  double price = 6;
  string status = 7;  // AVAILABLE, RESERVED, BOOKED
  int64 version = 8;
  string reserved_by = 9;
  int64 reserved_until = 10;  // Unix timestamp
}

message Reservation {
  string reservation_id = 1;
  int64 event_id = 2;
  string user_id = 3;
  repeated Seat seats = 4;
  int64 expires_at = 5;
  string status = 6;  // ACTIVE, CONFIRMED, EXPIRED
  int64 created_at = 7;
}

message GetAvailableSeatsRequest {
  int64 event_id = 1;
}

message GetAvailableSeatsResponse {
  repeated Seat seats = 1;
}

message ReserveSeatsRequest {
  int64 event_id = 1;
  repeated string seat_numbers = 2;
  string user_id = 3;
}

message ReserveSeatsResponse {
  Reservation reservation = 1;
}

// ... other messages
```

---

### Domain Models

**`internal/domain/seat.go`**:

```go
package domain

import "time"

type SeatStatus string

const (
    SeatAvailable SeatStatus = "AVAILABLE"
    SeatReserved  SeatStatus = "RESERVED"
    SeatBooked    SeatStatus = "BOOKED"
    SeatBlocked   SeatStatus = "BLOCKED"
)

type Seat struct {
    EventID       int64      `dynamodbav:"event_id"`
    SeatNumber    string     `dynamodbav:"seat_number"`
    Section       string     `dynamodbav:"section"`
    RowNumber     string     `dynamodbav:"row_number"`
    SeatType      string     `dynamodbav:"seat_type"`
    Price         float64    `dynamodbav:"price"`
    Status        SeatStatus `dynamodbav:"status"`
    Version       int64      `dynamodbav:"version"`
    ReservedBy    *string    `dynamodbav:"reserved_by,omitempty"`
    ReservedUntil *int64     `dynamodbav:"reserved_until,omitempty"`  // Unix timestamp
    BookingID     *string    `dynamodbav:"booking_id,omitempty"`
    CreatedAt     int64      `dynamodbav:"created_at"`
    UpdatedAt     int64      `dynamodbav:"updated_at"`
}

func (s *Seat) IsExpired() bool {
    if s.Status != SeatReserved || s.ReservedUntil == nil {
        return false
    }
    return time.Now().Unix() > *s.ReservedUntil
}
```

---

### DynamoDB Repository

**`internal/repository/dynamodb/seat_repository.go`**:

```go
package dynamodb

import (
    "context"
    "fmt"
    "time"

    "github.com/aws/aws-sdk-go-v2/aws"
    "github.com/aws/aws-sdk-go-v2/feature/dynamodb/attributevalue"
    "github.com/aws/aws-sdk-go-v2/feature/dynamodb/expression"
    "github.com/aws/aws-sdk-go-v2/service/dynamodb"
    "github.com/aws/aws-sdk-go-v2/service/dynamodb/types"

    "github.com/ticketing/inventory/internal/domain"
)

type SeatRepository struct {
    client    *dynamodb.Client
    tableName string
}

func NewSeatRepository(client *dynamodb.Client, tableName string) *SeatRepository {
    return &SeatRepository{
        client:    client,
        tableName: tableName,
    }
}

// GetAvailableSeats queries seats by event_id and status using GSI
func (r *SeatRepository) GetAvailableSeats(ctx context.Context, eventID int64) ([]*domain.Seat, error) {
    // Query using status-index GSI
    keyEx := expression.Key("event_id").Equal(expression.Value(eventID)).
        And(expression.Key("status").Equal(expression.Value("AVAILABLE")))

    expr, err := expression.NewBuilder().WithKeyCondition(keyEx).Build()
    if err != nil {
        return nil, fmt.Errorf("build expression: %w", err)
    }

    result, err := r.client.Query(ctx, &dynamodb.QueryInput{
        TableName:                 aws.String(r.tableName),
        IndexName:                 aws.String("status-index"),
        KeyConditionExpression:    expr.KeyCondition(),
        ExpressionAttributeNames:  expr.Names(),
        ExpressionAttributeValues: expr.Values(),
    })

    if err != nil {
        return nil, fmt.Errorf("query seats: %w", err)
    }

    var seats []*domain.Seat
    if err := attributevalue.UnmarshalListOfMaps(result.Items, &seats); err != nil {
        return nil, fmt.Errorf("unmarshal seats: %w", err)
    }

    return seats, nil
}

// GetSeat retrieves a specific seat
func (r *SeatRepository) GetSeat(ctx context.Context, eventID int64, seatNumber string) (*domain.Seat, error) {
    result, err := r.client.GetItem(ctx, &dynamodb.GetItemInput{
        TableName: aws.String(r.tableName),
        Key: map[string]types.AttributeValue{
            "event_id":    &types.AttributeValueMemberN{Value: fmt.Sprintf("%d", eventID)},
            "seat_number": &types.AttributeValueMemberS{Value: seatNumber},
        },
    })

    if err != nil {
        return nil, fmt.Errorf("get seat: %w", err)
    }

    if result.Item == nil {
        return nil, fmt.Errorf("seat not found")
    }

    var seat domain.Seat
    if err := attributevalue.UnmarshalMap(result.Item, &seat); err != nil {
        return nil, fmt.Errorf("unmarshal seat: %w", err)
    }

    return &seat, nil
}

// UpdateSeatStatus updates seat status with optimistic locking
func (r *SeatRepository) UpdateSeatStatus(
    ctx context.Context,
    eventID int64,
    seatNumber string,
    expectedVersion int64,
    newStatus domain.SeatStatus,
    reservedBy *string,
    reservedUntil *int64,
) error {
    now := time.Now().Unix()

    update := expression.Set(
        expression.Name("status"),
        expression.Value(newStatus),
    ).Set(
        expression.Name("version"),
        expression.Value(expectedVersion+1),
    ).Set(
        expression.Name("updated_at"),
        expression.Value(now),
    )

    if reservedBy != nil {
        update = update.Set(expression.Name("reserved_by"), expression.Value(*reservedBy))
    } else {
        update = update.Remove(expression.Name("reserved_by"))
    }

    if reservedUntil != nil {
        update = update.Set(expression.Name("reserved_until"), expression.Value(*reservedUntil))
    } else {
        update = update.Remove(expression.Name("reserved_until"))
    }

    // Condition: version matches AND status is AVAILABLE (prevents race)
    condition := expression.Name("version").Equal(expression.Value(expectedVersion)).
        And(expression.Name("status").Equal(expression.Value("AVAILABLE")))

    expr, err := expression.NewBuilder().
        WithUpdate(update).
        WithCondition(condition).
        Build()

    if err != nil {
        return fmt.Errorf("build expression: %w", err)
    }

    _, err = r.client.UpdateItem(ctx, &dynamodb.UpdateItemInput{
        TableName: aws.String(r.tableName),
        Key: map[string]types.AttributeValue{
            "event_id":    &types.AttributeValueMemberN{Value: fmt.Sprintf("%d", eventID)},
            "seat_number": &types.AttributeValueMemberS{Value: seatNumber},
        },
        UpdateExpression:          expr.Update(),
        ConditionExpression:       expr.Condition(),
        ExpressionAttributeNames:  expr.Names(),
        ExpressionAttributeValues: expr.Values(),
    })

    if err != nil {
        // Check if condition failed (concurrent update)
        var ccf *types.ConditionalCheckFailedException
        if errors.As(err, &ccf) {
            return fmt.Errorf("concurrent modification detected")
        }
        return fmt.Errorf("update seat: %w", err)
    }

    return nil
}

// ReserveSeatsTransaction reserves multiple seats atomically using DynamoDB Transactions
func (r *SeatRepository) ReserveSeatsTransaction(
    ctx context.Context,
    eventID int64,
    seatNumbers []string,
    userID string,
    reservedUntil int64,
) error {
    now := time.Now().Unix()

    // Build transaction items
    transactItems := make([]types.TransactWriteItem, 0, len(seatNumbers))

    for _, seatNumber := range seatNumbers {
        // Update expression
        update := expression.Set(
            expression.Name("status"),
            expression.Value("RESERVED"),
        ).Set(
            expression.Name("reserved_by"),
            expression.Value(userID),
        ).Set(
            expression.Name("reserved_until"),
            expression.Value(reservedUntil),
        ).Set(
            expression.Name("updated_at"),
            expression.Value(now),
        ).Add(
            expression.Name("version"),
            expression.Value(1),
        )

        // Condition: must be AVAILABLE
        condition := expression.Name("status").Equal(expression.Value("AVAILABLE"))

        expr, err := expression.NewBuilder().
            WithUpdate(update).
            WithCondition(condition).
            Build()

        if err != nil {
            return fmt.Errorf("build expression for %s: %w", seatNumber, err)
        }

        transactItems = append(transactItems, types.TransactWriteItem{
            Update: &types.Update{
                TableName: aws.String(r.tableName),
                Key: map[string]types.AttributeValue{
                    "event_id":    &types.AttributeValueMemberN{Value: fmt.Sprintf("%d", eventID)},
                    "seat_number": &types.AttributeValueMemberS{Value: seatNumber},
                },
                UpdateExpression:          expr.Update(),
                ConditionExpression:       expr.Condition(),
                ExpressionAttributeNames:  expr.Names(),
                ExpressionAttributeValues: expr.Values(),
            },
        })
    }

    // Execute transaction
    _, err := r.client.TransactWriteItems(ctx, &dynamodb.TransactWriteItemsInput{
        TransactItems: transactItems,
    })

    if err != nil {
        // Check if transaction canceled due to condition failure
        var txCanceled *types.TransactionCanceledException
        if errors.As(err, &txCanceled) {
            return fmt.Errorf("one or more seats not available")
        }
        return fmt.Errorf("transaction failed: %w", err)
    }

    return nil
}
```

---

### Redis Lock Repository

**`internal/repository/redis/lock_repository.go`**:

```go
package redis

import (
    "context"
    "crypto/rand"
    "encoding/base64"
    "errors"
    "time"

    "github.com/redis/go-redis/v9"
)

const (
    DefaultLockTTL = 30 * time.Second
)

type LockRepository struct {
    client *redis.ClusterClient
}

func NewLockRepository(client *redis.ClusterClient) *LockRepository {
    return &LockRepository{client: client}
}

// AcquireLock attempts to acquire a distributed lock
func (r *LockRepository) AcquireLock(ctx context.Context, resource string, ttl time.Duration) (string, error) {
    lockValue := generateLockValue()
    lockKey := "lock:seat:" + resource

    // Use SET NX EX (atomic set if not exists with expiration)
    success, err := r.client.SetNX(ctx, lockKey, lockValue, ttl).Result()
    if err != nil {
        return "", err
    }

    if !success {
        return "", errors.New("lock already held")
    }

    return lockValue, nil
}

// ReleaseLock releases the lock only if the value matches (Lua script for atomicity)
func (r *LockRepository) ReleaseLock(ctx context.Context, resource string, lockValue string) error {
    lockKey := "lock:seat:" + resource

    luaScript := `
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
    `

    _, err := r.client.Eval(ctx, luaScript, []string{lockKey}, lockValue).Result()
    return err
}

func generateLockValue() string {
    b := make([]byte, 16)
    rand.Read(b)
    return base64.URLEncoding.EncodeToString(b)
}
```

---

### Inventory Service (Business Logic)

**`internal/service/inventory_service.go`**:

```go
package service

import (
    "context"
    "fmt"
    "sort"
    "time"

    "github.com/google/uuid"
    "go.uber.org/zap"

    "github.com/ticketing/inventory/internal/domain"
    "github.com/ticketing/inventory/internal/repository/dynamodb"
    "github.com/ticketing/inventory/internal/repository/redis"
)

const (
    ReservationTTL = 10 * time.Minute
    LockTimeout    = 30 * time.Second
)

type InventoryService struct {
    seatRepo        *dynamodb.SeatRepository
    reservationRepo *dynamodb.ReservationRepository
    lockRepo        *redis.LockRepository
    logger          *zap.Logger
}

func NewInventoryService(
    seatRepo *dynamodb.SeatRepository,
    reservationRepo *dynamodb.ReservationRepository,
    lockRepo *redis.LockRepository,
    logger *zap.Logger,
) *InventoryService {
    return &InventoryService{
        seatRepo:        seatRepo,
        reservationRepo: reservationRepo,
        lockRepo:        lockRepo,
        logger:          logger,
    }
}

// GetAvailableSeats returns all available seats for an event
func (s *InventoryService) GetAvailableSeats(ctx context.Context, eventID int64) ([]*domain.Seat, error) {
    return s.seatRepo.GetAvailableSeats(ctx, eventID)
}

// ReserveSeats reserves multiple seats atomically with distributed locking
func (s *InventoryService) ReserveSeats(
    ctx context.Context,
    eventID int64,
    seatNumbers []string,
    userID string,
) (*domain.Reservation, error) {
    // Sort seat numbers to prevent deadlock
    sort.Strings(seatNumbers)

    // Acquire locks for all seats
    locks := make(map[string]string) // resource -> lockValue
    defer s.releaseLocks(ctx, locks)

    for _, seatNumber := range seatNumbers {
        resource := fmt.Sprintf("%d:%s", eventID, seatNumber)
        lockValue, err := s.lockRepo.AcquireLock(ctx, resource, LockTimeout)
        if err != nil {
            s.logger.Error("failed to acquire lock",
                zap.String("resource", resource),
                zap.Error(err),
            )
            return nil, fmt.Errorf("seat %s is being processed", seatNumber)
        }
        locks[resource] = lockValue
    }

    // Reserve seats using DynamoDB Transaction
    reservedUntil := time.Now().Add(ReservationTTL).Unix()
    err := s.seatRepo.ReserveSeatsTransaction(ctx, eventID, seatNumbers, userID, reservedUntil)
    if err != nil {
        return nil, err
    }

    // Create reservation record
    reservationID := uuid.New().String()
    reservation := &domain.Reservation{
        ReservationID: reservationID,
        EventID:       eventID,
        UserID:        userID,
        SeatNumbers:   seatNumbers,
        ExpiresAt:     reservedUntil,
        Status:        "ACTIVE",
        CreatedAt:     time.Now().Unix(),
    }

    err = s.reservationRepo.Create(ctx, reservation)
    if err != nil {
        // Rollback seat reservations (would need compensating logic here)
        return nil, fmt.Errorf("failed to create reservation: %w", err)
    }

    return reservation, nil
}

func (s *InventoryService) releaseLocks(ctx context.Context, locks map[string]string) {
    for resource, lockValue := range locks {
        if err := s.lockRepo.ReleaseLock(ctx, resource, lockValue); err != nil {
            s.logger.Error("failed to release lock",
                zap.String("resource", resource),
                zap.Error(err),
            )
        }
    }
}
```

---

## 🚀 Kubernetes Deployment

**`k8s/deployment.yaml`**:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inventory-service
  namespace: ticketing-prod
spec:
  replicas: 5
  selector:
    matchLabels:
      app: inventory-service
  template:
    metadata:
      labels:
        app: inventory-service
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
    spec:
      serviceAccountName: inventory-service
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: workload
                operator: In
                values:
                - inventory
      tolerations:
      - key: workload
        operator: Equal
        value: inventory
        effect: NoSchedule
      containers:
      - name: inventory-service
        image: 123456789.dkr.ecr.us-east-1.amazonaws.com/inventory-service:v1.0.0
        ports:
        - containerPort: 8080
          name: grpc
          protocol: TCP
        - containerPort: 9090
          name: metrics
          protocol: TCP
        env:
        - name: AWS_REGION
          value: us-east-1
        - name: DYNAMODB_TABLE_SEATS
          value: seats-prod
        - name: DYNAMODB_TABLE_RESERVATIONS
          value: reservations-prod
        - name: REDIS_ADDRS
          value: "ticketing-redis.cache.amazonaws.com:6379"
        - name: DD_AGENT_HOST
          valueFrom:
            fieldRef:
              fieldPath: status.hostIP
        - name: DD_SERVICE
          value: inventory-service
        - name: DD_VERSION
          value: v1.0.0
        - name: DD_ENV
          value: production
        resources:
          requests:
            memory: "512Mi"
            cpu: "1000m"
          limits:
            memory: "1Gi"
            cpu: "2000m"
        livenessProbe:
          grpc:
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          grpc:
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: inventory-service
  namespace: ticketing-prod
spec:
  selector:
    app: inventory-service
  ports:
  - name: grpc
    port: 8080
    targetPort: 8080
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: inventory-service-hpa
  namespace: ticketing-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: inventory-service
  minReplicas: 5
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: grpc_request_duration_seconds
      target:
        type: AverageValue
        averageValue: "500m"  # 500ms
```

---

## 🎯 Success Criteria

- [ ] gRPC service accepts requests
- [ ] DynamoDB queries execute in <50ms
- [ ] Redis locks acquired successfully
- [ ] DynamoDB Transactions prevent concurrent updates
- [ ] Reservation TTL expires correctly
- [ ] HPA scales from 5 to 50 pods under load
- [ ] Datadog shows distributed traces
- [ ] Zero double-booking in load tests

## 📊 Estimated Timeline
**5-7 days**

## 🔗 Dependencies
- **Previous**: [Phase 1: K8s & DynamoDB](./Phase-1-K8s-DynamoDB.md)

---

## 📌 Notes
- **DynamoDB Transactions** support up to 100 items per transaction
- **Redis Cluster** requires consistent hashing for lock keys
- **gRPC** provides ~10x lower latency than REST
- **Datadog APM** automatically traces gRPC calls
- **HPA** should target 70% CPU to leave headroom for spikes
