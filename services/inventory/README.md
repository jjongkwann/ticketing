# Inventory Service (Go + gRPC)

고성능 좌석 재고 관리 서비스 - DynamoDB + Redis 기반 분산 시스템

## 주요 기능

### 1. 좌석 예약 시스템
- **DynamoDB 조건부 쓰기**: Optimistic Locking으로 동시성 제어
- **Redis 분산 락**: 좌석 단위 잠금으로 이중 예약 방지
- **TTL 기반 예약 만료**: DynamoDB TTL로 자동 정리

### 2. 다층 동시성 제어
```
Layer 1: Redis 분산 락 (좌석 단위)
  └─> Layer 2: DynamoDB 조건부 쓰기 (Version 기반)
      └─> Layer 3: DynamoDB Transactions (다중 좌석 예약)
```

### 3. 아키텍처
```
┌─────────────┐
│   Booking   │ (FastAPI)
│   Service   │
└──────┬──────┘
       │ gRPC
       ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Inventory  │─────▶│  DynamoDB   │      │    Redis    │
│   Service   │      │   (Seats)   │      │  (Locks)    │
│   (Go)      │      └─────────────┘      └─────────────┘
└─────────────┘              │
       │                     │
       │              DynamoDB Streams
       │                     │
       ▼                     ▼
┌─────────────┐      ┌─────────────┐
│ Prometheus  │      │   Kafka     │
│  (Metrics)  │      │  (Events)   │
└─────────────┘      └─────────────┘
```

## 프로젝트 구조

```
inventory/
├── cmd/
│   └── server/
│       └── main.go                 # 엔트리 포인트
├── internal/
│   ├── config/
│   │   └── config.go               # 환경 설정
│   ├── models/
│   │   └── models.go               # 데이터 모델
│   ├── repository/
│   │   ├── dynamodb.go             # DynamoDB 레포지토리
│   │   └── redis.go                # Redis 레포지토리
│   ├── service/
│   │   └── inventory.go            # 비즈니스 로직
│   ├── grpc/
│   │   └── server.go               # gRPC 서버
│   └── http/
│       └── server.go               # HTTP 서버 (health/metrics)
├── proto/
│   └── inventory.proto             # gRPC API 정의
├── go.mod
├── go.sum
├── Dockerfile
└── .env.example
```

## DynamoDB 테이블 스키마

### Seats Table
```
PK: event_id (String)
SK: seat_number (String)
Attributes:
  - status (String): AVAILABLE | RESERVED | BOOKED
  - user_id (String, optional)
  - price (Number)
  - reserved_at (Number, Unix timestamp)
  - version (Number): Optimistic locking version
  - created_at (Number)
  - updated_at (Number)

GSI: status-index
  PK: event_id
  SK: status
```

### Reservations Table
```
PK: reservation_id (String, UUID)
Attributes:
  - event_id (String)
  - seat_number (String)
  - user_id (String)
  - price (Number)
  - created_at (Number)
  - expires_at (Number): TTL attribute
  - status (String): PENDING | CONFIRMED | CANCELLED | EXPIRED

GSI: event-index
  PK: event_id

GSI: user-index
  PK: user_id
```

### Bookings Table
```
PK: booking_id (String, UUID)
Attributes:
  - event_id (String)
  - seat_number (String)
  - user_id (String)
  - price (Number)
  - payment_id (String)
  - created_at (Number)
  - status (String): CONFIRMED | CANCELLED

GSI: event-index
  PK: event_id

GSI: user-index
  PK: user_id
```

## gRPC API

### ReserveSeat
좌석 예약 (분산 락 + 조건부 쓰기)

```protobuf
rpc ReserveSeat(ReserveSeatRequest) returns (ReserveSeatResponse);

message ReserveSeatRequest {
  string event_id = 1;
  string seat_number = 2;
  string user_id = 3;
}

message ReserveSeatResponse {
  bool success = 1;
  string message = 2;
  Seat seat = 3;
  string reservation_id = 4;
}
```

**예약 플로우**:
1. Redis 분산 락 획득 (`SETNX key token EX 30`)
2. DynamoDB 좌석 조회 (현재 상태 + version 확인)
3. 조건부 업데이트 (`status = AVAILABLE AND version = :current`)
4. Reservations 테이블에 레코드 생성 (TTL 설정)
5. Redis 락 해제

### ConfirmBooking
예약 확정 (결제 완료 후)

```protobuf
rpc ConfirmBooking(ConfirmBookingRequest) returns (ConfirmBookingResponse);

message ConfirmBookingRequest {
  string reservation_id = 1;
  string user_id = 2;
  string payment_id = 3;
}
```

**확정 플로우**:
1. Reservation 조회 및 유효성 검증
2. Redis 락 획득
3. Seat 상태를 BOOKED로 업데이트
4. Bookings 테이블에 레코드 생성
5. Reservation 상태를 CONFIRMED로 업데이트

## 빌드 및 실행

### 로컬 개발

```bash
# Protobuf 컴파일 (최초 1회)
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest

protoc --go_out=. --go_opt=paths=source_relative \
  --go-grpc_out=. --go-grpc_opt=paths=source_relative \
  proto/inventory.proto

# Dependencies 다운로드
go mod download

# 실행 (환경 변수 필요)
go run cmd/server/main.go
```

### Docker 빌드

```bash
docker build -t inventory-service:latest .

docker run -p 50051:50051 -p 8080:8080 \
  --env-file .env \
  inventory-service:latest
```

### Kubernetes 배포

```bash
# ECR에 푸시
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

docker tag inventory-service:latest $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ticketing/inventory-service:latest
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ticketing/inventory-service:latest

# Kubernetes 배포
kubectl apply -f ../../k8s/services/inventory-service.yaml
```

## 성능 최적화

### 1. Redis 연결 풀
```go
redisClient := redis.NewClient(&redis.Options{
    Addr:         cfg.RedisEndpoint,
    PoolSize:     100,
    MinIdleConns: 20,
})
```

### 2. DynamoDB 배치 작업
- `BatchWriteItem`: 좌석 초기화 시 25개씩 배치 처리
- `ParallelScan`: 대량 조회 시 병렬 스캔

### 3. 고루틴 활용
- 예약 만료 정리: 백그라운드 고루틴
- gRPC 동시 요청 처리: Go 네이티브 동시성

## 모니터링

### Prometheus 메트릭

```go
// HTTP 엔드포인트: :8080/metrics

http_requests_total{method, endpoint, status}
http_request_duration_seconds{method, endpoint}
dynamodb_operation_duration_seconds{operation, table}
redis_command_duration_seconds{command}
seat_reservations_total{event_id, status}
```

### 헬스체크

```bash
# Liveness
curl http://localhost:8080/health

# Readiness
curl http://localhost:8080/ready
```

## 에러 처리

### 동시성 에러
- `ErrSeatAlreadyReserved`: 좌석이 이미 예약됨
- `ErrVersionMismatch`: 동시 수정 감지됨 (optimistic lock 실패)
- `ErrLockAlreadyHeld`: Redis 락이 이미 다른 클라이언트에게 점유됨

### 재시도 정책
- DynamoDB 조건부 쓰기 실패: 재시도 없음 (실패 반환)
- Redis 락 획득 실패: 최대 3회 재시도 (100ms 간격)
- 네트워크 오류: Exponential backoff

## 보안

### IAM Roles (IRSA)
```yaml
# Kubernetes ServiceAccount annotation
eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT_ID:role/inventory-service-role
```

### IAM 정책
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query",
        "dynamodb:BatchWriteItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/ticketing-seats-*",
        "arn:aws:dynamodb:*:*:table/ticketing-reservations-*",
        "arn:aws:dynamodb:*:*:table/ticketing-bookings-*"
      ]
    }
  ]
}
```

## 테스트

```bash
# Unit tests
go test ./internal/...

# Integration tests (DynamoDB Local + Redis)
docker-compose -f docker-compose.test.yml up -d
go test -tags=integration ./...
```

## 트러블슈팅

### 좌석 예약 실패
```bash
# DynamoDB 좌석 상태 확인
aws dynamodb get-item \
  --table-name ticketing-seats-prod \
  --key '{"event_id": {"S": "EVENT_ID"}, "seat_number": {"S": "S-0001"}}'

# Redis 락 확인
redis-cli GET "lock:seat:EVENT_ID:S-0001"
```

### 성능 저하
```bash
# DynamoDB 메트릭
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=ticketing-seats-prod \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 3600 \
  --statistics Sum

# Redis 메트릭
redis-cli INFO stats
```

## 라이선스

Proprietary - Ticketing System
