# Ticketing System - Production Architecture

> **Enterprise-grade ticketing system with DynamoDB, Kubernetes, Kafka**
>
> Designed for: **500k concurrent users, 10k+ bookings/sec, zero double-booking**

---

## 🏗️ Technology Stack (Production)

### Backend Services
- **Go** - Inventory Service (high-concurrency seat management)
- **Python 3.11+ / FastAPI** - Other microservices
- **gRPC** - Inter-service communication (low latency)
- **REST API** - External client communication

### Databases
- **MySQL 8.0** - Relational data (Events, Users, Auth)
- **DynamoDB** - High-throughput data (Seats, Reservations, Bookings)
- **Redis 7.0** - Distributed locks, caching, rate limiting
- **Elasticsearch 8.0** - Event search and discovery

### Messaging & Streaming
- **Apache Kafka** - Event streaming, CDC (Change Data Capture)
- **Kafka Connect** - DynamoDB Streams → Kafka → Elasticsearch

### Orchestration & Deployment
- **Kubernetes (EKS)** - Container orchestration
- **Helm Charts** - Application packaging
- **Github Actions** - CI pipeline
- **Spinnaker** - CD pipeline (blue/green, canary deployments)
- **Gitploy** - Deployment tracking and rollback

### Monitoring & Observability
- **Datadog** - APM, distributed tracing, metrics, logs
- **Prometheus** - Metrics collection and alerting
- **Grafana** - Custom dashboards
- **Loki** - Log aggregation
- **AWS CloudWatch** - AWS resource monitoring

### ML/MLOps (Future)
- **AWS Sagemaker** - Dynamic pricing models
- **Triton** - Model serving
- **MLFlow** - Experiment tracking
- **PyTorch** - Price prediction models

---

## 📊 Database Architecture

### Hybrid Database Strategy

```
┌─────────────────────────────────────────────────────────┐
│                  Application Services                   │
└─────────────────────────────────────────────────────────┘
         │                    │                    │
    ┌────┴────┐         ┌─────┴─────┐         ┌────┴────┐
    │  MySQL  │         │ DynamoDB  │         │  Redis  │
    │(Events, │         │(Seats,    │         │ (Locks, │
    │ Users)  │         │ Bookings) │         │ Cache)  │
    └─────────┘         └───────────┘         └─────────┘
         │                    │
         │              DynamoDB Streams
         │                    │
         └────────┬───────────┘
                  │
            ┌─────┴─────┐
            │   Kafka   │
            │ (CDC Bus) │
            └───────────┘
                  │
         ┌────────┴────────┐
         │                 │
   Elasticsearch      Analytics DB
```

### MySQL Tables (Relational Data)

**Purpose**: Metadata, user management, auth

```sql
-- Database: ticketing_main

-- Users (authentication)
CREATE TABLE users (
    user_id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Events (metadata only, not seat inventory)
CREATE TABLE events (
    event_id BIGSERIAL PRIMARY KEY,
    event_name VARCHAR(255) NOT NULL,
    event_date TIMESTAMP NOT NULL,
    venue_name VARCHAR(255),
    total_seats INT NOT NULL,
    available_seats INT NOT NULL,  -- Cached from DynamoDB
    status VARCHAR(20) NOT NULL,  -- UPCOMING, ON_SALE, SOLD_OUT, CANCELLED
    sale_start_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
CREATE INDEX idx_events_status ON events(status);
CREATE INDEX idx_events_date ON events(event_date);

-- Outbox pattern for Kafka
CREATE TABLE outbox_events (
    id BIGSERIAL PRIMARY KEY,
    aggregate_id BIGINT NOT NULL,
    aggregate_type VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);
CREATE INDEX idx_outbox_processed ON outbox_events(processed, created_at);
```

---

### DynamoDB Tables (High-Throughput Data)

**Purpose**: Seat inventory, reservations, bookings (hot path)

#### Table 1: `seats`

**Access Patterns**:
1. Get all available seats for an event
2. Get specific seat details
3. Update seat status with optimistic locking

```json
{
  "TableName": "seats",
  "KeySchema": [
    { "AttributeName": "event_id", "KeyType": "HASH" },
    { "AttributeName": "seat_number", "KeyType": "RANGE" }
  ],
  "AttributeDefinitions": [
    { "AttributeName": "event_id", "AttributeType": "N" },
    { "AttributeName": "seat_number", "AttributeType": "S" },
    { "AttributeName": "status", "AttributeType": "S" }
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "status-index",
      "KeySchema": [
        { "AttributeName": "event_id", "KeyType": "HASH" },
        { "AttributeName": "status", "KeyType": "RANGE" }
      ],
      "Projection": { "ProjectionType": "ALL" }
    }
  ],
  "BillingMode": "PAY_PER_REQUEST",  // or PROVISIONED with auto-scaling
  "StreamSpecification": {
    "StreamEnabled": true,
    "StreamViewType": "NEW_AND_OLD_IMAGES"
  }
}
```

**Item Structure**:
```json
{
  "event_id": 987,
  "seat_number": "A1",
  "section": "VIP",
  "row_number": "A",
  "seat_type": "VIP",
  "price": 150.00,
  "status": "AVAILABLE",  // AVAILABLE, RESERVED, BOOKED, BLOCKED
  "version": 5,  // Optimistic locking
  "reserved_by": "user_123",  // null if available
  "reserved_until": 1700000000,  // Unix timestamp
  "booking_id": null,
  "created_at": 1699000000,
  "updated_at": 1699500000
}
```

#### Table 2: `reservations`

**Access Patterns**:
1. Get user's active reservations
2. Find expired reservations for cleanup
3. Get reservation by ID

```json
{
  "TableName": "reservations",
  "KeySchema": [
    { "AttributeName": "reservation_id", "KeyType": "HASH" }
  ],
  "AttributeDefinitions": [
    { "AttributeName": "reservation_id", "AttributeType": "S" },
    { "AttributeName": "user_id", "AttributeType": "S" },
    { "AttributeName": "expires_at", "AttributeType": "N" },
    { "AttributeName": "status", "AttributeType": "S" }
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "user-reservations-index",
      "KeySchema": [
        { "AttributeName": "user_id", "KeyType": "HASH" },
        { "AttributeName": "expires_at", "KeyType": "RANGE" }
      ],
      "Projection": { "ProjectionType": "ALL" }
    },
    {
      "IndexName": "expiry-index",
      "KeySchema": [
        { "AttributeName": "status", "KeyType": "HASH" },
        { "AttributeName": "expires_at", "KeyType": "RANGE" }
      ],
      "Projection": { "ProjectionType": "ALL" }
    }
  ],
  "BillingMode": "PAY_PER_REQUEST",
  "TimeToLiveSpecification": {
    "Enabled": true,
    "AttributeName": "ttl"  // Auto-delete after 24 hours
  }
}
```

#### Table 3: `bookings`

**Access Patterns**:
1. Get user's bookings
2. Get booking by reference
3. Get booking by ID

```json
{
  "TableName": "bookings",
  "KeySchema": [
    { "AttributeName": "booking_id", "KeyType": "HASH" }
  ],
  "AttributeDefinitions": [
    { "AttributeName": "booking_id", "AttributeType": "S" },
    { "AttributeName": "user_id", "AttributeType": "S" },
    { "AttributeName": "booking_reference", "AttributeType": "S" },
    { "AttributeName": "created_at", "AttributeType": "N" }
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "user-bookings-index",
      "KeySchema": [
        { "AttributeName": "user_id", "KeyType": "HASH" },
        { "AttributeName": "created_at", "KeyType": "RANGE" }
      ],
      "Projection": { "ProjectionType": "ALL" }
    },
    {
      "IndexName": "reference-index",
      "KeySchema": [
        { "AttributeName": "booking_reference", "KeyType": "HASH" }
      ],
      "Projection": { "ProjectionType": "ALL" }
    }
  ],
  "BillingMode": "PAY_PER_REQUEST"
}
```

**Item Structure**:
```json
{
  "booking_id": "bk_abc123",
  "booking_reference": "BK-2025-001234",
  "event_id": 987,
  "user_id": "user_123",
  "seats": [
    { "seat_id": "987#A1", "seat_number": "A1", "price": 150.00 },
    { "seat_id": "987#A2", "seat_number": "A2", "price": 150.00 }
  ],
  "total_amount": 300.00,
  "status": "CONFIRMED",  // PENDING, CONFIRMED, CANCELLED, FAILED
  "payment_id": "pay_xyz789",
  "payment_status": "SUCCESS",
  "created_at": 1699600000,
  "confirmed_at": 1699600050
}
```

---

## 🔒 Concurrency Control (Multi-Layer)

### Layer 1: Redis Distributed Locks
```
Lock Key: lock:seat:{event_id}:{seat_number}
TTL: 30 seconds
Algorithm: Redlock (for Redis Cluster)
```

### Layer 2: DynamoDB Conditional Writes
```python
# Optimistic locking with version number
update_item(
    Key={'event_id': 987, 'seat_number': 'A1'},
    UpdateExpression='SET #status = :new_status, version = version + :inc',
    ConditionExpression='version = :expected_version AND #status = :old_status',
    ExpressionAttributeNames={'#status': 'status'},
    ExpressionAttributeValues={
        ':expected_version': 5,
        ':new_status': 'RESERVED',
        ':old_status': 'AVAILABLE',
        ':inc': 1
    }
)
# Raises ConditionalCheckFailedException on conflict
```

### Layer 3: DynamoDB Transactions
```python
# Atomic multi-seat reservation
transact_write_items(
    TransactItems=[
        {
            'Update': {
                'TableName': 'seats',
                'Key': {'event_id': 987, 'seat_number': 'A1'},
                'UpdateExpression': 'SET #status = :reserved, reserved_by = :user',
                'ConditionExpression': '#status = :available'
            }
        },
        {
            'Put': {
                'TableName': 'reservations',
                'Item': {...}
            }
        }
    ]
)
```

---

## 🔄 Event-Driven Architecture with Kafka

```
DynamoDB Streams → Kafka Connect → Kafka Topics → Consumers

Topics:
- seat.status.changed (CDC from seats table)
- booking.confirmed
- reservation.expired
- event.created/updated

Consumers:
- Elasticsearch Indexer
- Analytics Service
- Notification Service
- Metrics Aggregator
```

**Kafka Configuration**:
```yaml
kafka:
  brokers: ["kafka-0.kafka:9092", "kafka-1.kafka:9092", "kafka-2.kafka:9092"]
  topics:
    seat_events:
      partitions: 10
      replication_factor: 3
    booking_events:
      partitions: 5
      replication_factor: 3
```

---

## ☸️ Kubernetes Architecture

### Namespace Structure
```
ticketing-prod
├── api-gateway
├── auth-service
├── events-service
├── inventory-service (Go)
├── booking-service
├── payment-service
├── search-service
└── notification-service
```

### Sample Deployment (Inventory Service)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inventory-service
  namespace: ticketing-prod
  labels:
    app: inventory-service
    version: v1.2.3
spec:
  replicas: 5  # Horizontal scaling
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 2
      maxUnavailable: 0
  selector:
    matchLabels:
      app: inventory-service
  template:
    metadata:
      labels:
        app: inventory-service
        version: v1.2.3
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: inventory-service
        image: 123456789.dkr.ecr.us-east-1.amazonaws.com/inventory-service:v1.2.3
        ports:
        - containerPort: 8080  # gRPC
          name: grpc
        - containerPort: 8081  # HTTP (health checks)
          name: http
        env:
        - name: DYNAMODB_TABLE_SEATS
          value: "seats-prod"
        - name: REDIS_CLUSTER_ENDPOINTS
          valueFrom:
            configMapKeyRef:
              name: redis-config
              key: endpoints
        - name: DD_AGENT_HOST
          valueFrom:
            fieldRef:
              fieldPath: status.hostIP
        - name: DD_SERVICE
          value: "inventory-service"
        - name: DD_VERSION
          value: "v1.2.3"
        resources:
          requests:
            memory: "256Mi"
            cpu: "500m"
          limits:
            memory: "512Mi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8081
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8081
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
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## 📈 Monitoring & Observability

### Datadog Integration

```go
// Go service instrumentation
import (
    "gopkg.in/DataDog/dd-trace-go.v1/ddtrace/tracer"
    "gopkg.in/DataDog/dd-trace-go.v1/profiler"
)

func main() {
    tracer.Start(
        tracer.WithService("inventory-service"),
        tracer.WithEnv("prod"),
        tracer.WithServiceVersion("v1.2.3"),
    )
    defer tracer.Stop()

    profiler.Start(
        profiler.WithService("inventory-service"),
        profiler.WithProfileTypes(
            profiler.CPUProfile,
            profiler.HeapProfile,
        ),
    )
    defer profiler.Stop()
}
```

### Prometheus Metrics

```go
import "github.com/prometheus/client_golang/prometheus"

var (
    seatReservationDuration = prometheus.NewHistogram(
        prometheus.HistogramOpts{
            Name: "seat_reservation_duration_seconds",
            Help: "Time taken to reserve a seat",
            Buckets: prometheus.DefBuckets,
        },
    )

    lockAcquisitionFailures = prometheus.NewCounter(
        prometheus.CounterOpts{
            Name: "redis_lock_acquisition_failures_total",
            Help: "Total number of Redis lock acquisition failures",
        },
    )
)
```

### Grafana Dashboards

**Key Metrics**:
- Seat reservation latency (p50, p95, p99)
- Lock acquisition success rate
- DynamoDB read/write capacity utilization
- Redis memory usage
- Active reservations count
- Booking success rate

---

## 🚀 CI/CD Pipeline

### Github Actions (CI)

```yaml
name: CI - Inventory Service

on:
  push:
    branches: [main, develop]
    paths:
      - 'services/inventory/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      - name: Run tests
        run: |
          cd services/inventory
          go test -v -race -coverprofile=coverage.out ./...
      - name: Upload coverage to Datadog
        run: |
          datadog-ci test upload --service=inventory-service coverage.out

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: |
          docker build -t inventory-service:${{ github.sha }} .
      - name: Push to ECR
        run: |
          aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
          docker tag inventory-service:${{ github.sha }} $ECR_REGISTRY/inventory-service:${{ github.sha }}
          docker push $ECR_REGISTRY/inventory-service:${{ github.sha }}
```

### Spinnaker (CD)

**Pipeline Stages**:
1. **Bake**: Create K8s manifests with new image tag
2. **Deploy to Staging**: Kubernetes deployment
3. **Integration Tests**: Run E2E tests
4. **Manual Judgment**: Approve production deploy
5. **Canary Deploy**: 10% → 50% → 100%
6. **Monitor**: Check Datadog metrics for errors
7. **Rollback**: Automatic on error rate spike

---

## 🎯 Performance Targets (Production SLA)

| Metric | Target | Monitoring |
|--------|--------|------------|
| Seat availability query | <100ms (p99) | Datadog APM |
| Seat reservation | <500ms (p99) | Datadog APM |
| Lock acquisition | <50ms (p99) | Prometheus |
| DynamoDB read latency | <10ms (p99) | CloudWatch |
| DynamoDB write latency | <20ms (p99) | CloudWatch |
| gRPC call latency | <50ms (p99) | Datadog |
| Kafka lag | <5 seconds | Prometheus |
| Service availability | 99.95% | Datadog SLOs |
| Zero double-booking | **100%** | Custom metric |

---

## 📦 Next Steps

Proceed to updated phase documentation:
- **[Phase 1: Kubernetes & DynamoDB Infrastructure](./Phase-1-K8s-DynamoDB.md)**
- **[Phase 3: Go Inventory Service (DynamoDB)](./Phase-3-Inventory-DynamoDB.md)**

---

<div align="center">

**Production-Ready Ticketing System**

*Built for scale with DynamoDB, Kubernetes, and Kafka*

</div>
