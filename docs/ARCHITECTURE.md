# System Architecture Documentation

## 목차

1. [시스템 개요](#시스템-개요)
2. [아키텍처 원칙](#아키텍처-원칙)
3. [시스템 아키텍처](#시스템-아키텍처)
4. [마이크로서비스 상세](#마이크로서비스-상세)
5. [데이터베이스 설계](#데이터베이스-설계)
6. [이벤트 기반 아키텍처](#이벤트-기반-아키텍처)
7. [보안 아키텍처](#보안-아키텍처)
8. [확장성 전략](#확장성-전략)
9. [고가용성 설계](#고가용성-설계)
10. [기술 스택](#기술-스택)

---

## 시스템 개요

Ticketing Pro는 **마이크로서비스 아키텍처** 기반의 대규모 티켓 예매 플랫폼입니다.

### 핵심 요구사항

| 요구사항 | 목표 |
|---------|------|
| **처리량** | 10,000+ bookings/second |
| **동시 접속** | 100,000+ concurrent users |
| **가용성** | 99.9% uptime |
| **지연시간** | < 200ms (p95) |
| **데이터** | Petabyte-scale event data |

### 주요 기능

1. **실시간 좌석 예약**: 분산 락을 통한 동시성 제어
2. **Virtual Waiting Room**: 공정한 티켓 판매를 위한 대기열 시스템
3. **SafeTix**: 위조 방지 동적 QR 코드
4. **이벤트 검색**: OpenSearch 기반 전문 검색
5. **결제 처리**: Stripe 통합 PCI DSS 준수

---

## 아키텍처 원칙

### 1. 마이크로서비스

각 비즈니스 도메인을 독립적인 서비스로 분리:
- **독립 배포**: 서비스별 독립적 릴리스
- **기술 다양성**: 서비스별 최적 기술 선택 (Python, Go)
- **장애 격리**: 한 서비스 장애가 전체 시스템에 영향 최소화

### 2. 이벤트 기반

서비스 간 느슨한 결합:
- **Kafka**: 이벤트 스트리밍 플랫폼
- **비동기 통신**: 서비스 간 의존성 최소화
- **이벤트 소싱**: 상태 변경을 이벤트로 기록

### 3. API Gateway 패턴

단일 진입점:
- **라우팅**: 요청을 적절한 서비스로 라우팅
- **Rate Limiting**: 서비스별 요청 제한
- **인증**: JWT 토큰 검증

### 4. CQRS (Command Query Responsibility Segregation)

읽기/쓰기 분리:
- **Command**: PostgreSQL/DynamoDB (쓰기 최적화)
- **Query**: OpenSearch (읽기 최적화)

### 5. 분산 트랜잭션

Saga 패턴:
- **Choreography**: 이벤트 기반 saga
- **보상 트랜잭션**: 실패 시 rollback

---

## 시스템 아키텍처

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                         Users                                 │
└───────────┬──────────────────────────────────────────────────┘
            │
            ├─────────────────┬────────────────┐
            │                 │                │
    ┌───────▼──────┐  ┌──────▼──────┐  ┌─────▼──────┐
    │  Web Browser │  │ Mobile App  │  │  Partners  │
    │   (React)    │  │  (Flutter)  │  │    (API)   │
    └───────┬──────┘  └──────┬──────┘  └─────┬──────┘
            │                 │                │
            └─────────────────┼────────────────┘
                              │
                     ┌────────▼────────┐
                     │   CloudFront    │
                     │      (CDN)      │
                     └────────┬────────┘
                              │
                  ┌───────────┴───────────┐
                  │                       │
          ┌───────▼──────┐       ┌───────▼────────┐
          │      S3      │       │      ALB       │
          │   (Static)   │       │ (Load Balancer)│
          └──────────────┘       └───────┬────────┘
                                         │
                                ┌────────▼────────┐
                                │  API Gateway    │
                                │   (FastAPI)     │
                                └────────┬────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        │                                │                                │
┌───────▼──────┐              ┌─────────▼────────┐           ┌──────────▼────────┐
│Auth Service  │              │ Events Service   │           │ Booking Service   │
│ (FastAPI)    │              │   (FastAPI)      │           │   (FastAPI)       │
│              │              │                  │           │                   │
│ PostgreSQL   │              │   PostgreSQL     │           │    DynamoDB       │
└───────┬──────┘              └─────────┬────────┘           └──────────┬────────┘
        │                               │                                │
        │                     ┌─────────▼────────┐           ┌──────────▼────────┐
        │                     │ Search Service   │           │ Payment Service   │
        │                     │   (FastAPI)      │           │   (FastAPI)       │
        │                     │                  │           │                   │
        │                     │   OpenSearch     │           │     Stripe        │
        │                     └─────────┬────────┘           └──────────┬────────┘
        │                               │                                │
        │                     ┌─────────▼────────┐           ┌──────────▼────────┐
        │                     │Inventory Service │           │Notification Svc   │
        │                     │      (Go)        │           │   (FastAPI)       │
        │                     │                  │           │                   │
        │                     │    PostgreSQL    │           │   SES/SNS         │
        └─────────────────────┴──────────────────┴───────────┴───────────────────┘
                                         │
                                ┌────────▼────────┐
                                │      Kafka      │
                                │ (Event Stream)  │
                                └─────────────────┘
                                         │
                                ┌────────▼────────┐
                                │     Redis       │
                                │  (Cache/Lock)   │
                                └─────────────────┘
```

### 서비스 간 통신

```
┌─────────────┐     REST API      ┌──────────────┐
│   Client    │ ────────────────> │ API Gateway  │
└─────────────┘                   └──────┬───────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
              REST  │              REST  │              REST  │
                    ▼                    ▼                    ▼
           ┌────────────────┐   ┌────────────────┐  ┌────────────────┐
           │ Auth Service   │   │Events Service  │  │Booking Service │
           └────────┬───────┘   └────────┬───────┘  └────────┬───────┘
                    │                    │                    │
                    │                    │                    │
           Kafka    │           Kafka    │           Kafka    │
           Events   │           Events   │           Events   │
                    │                    │                    │
                    └────────────────────┼────────────────────┘
                                         │
                                    ┌────▼─────┐
                                    │   Kafka  │
                                    └──────────┘
```

### 데이터 흐름

**예매 플로우 (Booking Flow):**

```
User → API Gateway → Booking Service
                           │
                           ├─→ Inventory Service (gRPC) - Reserve Seats
                           │        │
                           │        └─→ Redis Lock (Distributed Lock)
                           │
                           ├─→ DynamoDB - Create Booking
                           │
                           ├─→ Kafka - BookingCreated Event
                           │        │
                           │        ├─→ Payment Service - Create Payment Intent
                           │        ├─→ Notification Service - Send Email
                           │        └─→ Search Service - Update Index
                           │
                           └─→ Return booking_id + payment_intent
```

**결제 플로우 (Payment Flow):**

```
User → Stripe.js (Client-side)
           │
           └─→ Stripe API - Process Payment
                     │
                     └─→ Webhook → Payment Service
                                      │
                                      ├─→ Kafka - PaymentSucceeded Event
                                      │        │
                                      │        ├─→ Booking Service - Confirm Booking
                                      │        │        │
                                      │        │        └─→ Inventory Service - Confirm Seats
                                      │        │
                                      │        └─→ Notification Service - Send Ticket
                                      │
                                      └─→ Return confirmation
```

---

## 마이크로서비스 상세

### 1. API Gateway

**책임:**
- 요청 라우팅
- Rate limiting (10-100 req/min depending on endpoint)
- JWT 토큰 검증
- CORS 처리

**기술:**
- FastAPI
- SlowAPI (rate limiting)
- httpx (service proxy)

**라우팅 규칙:**
```python
/api/auth/*      → Auth Service
/api/events/*    → Events Service
/api/bookings/*  → Booking Service
/api/payment/*   → Payment Service
/api/search/*    → Search Service
/api/queue/*     → Queue Service (Redis)
```

**Rate Limits:**
- POST /auth/login: 10 req/min
- POST /auth/register: 5 req/min
- POST /bookings: 20 req/min
- GET /events: 100 req/min

---

### 2. Auth Service

**책임:**
- 사용자 회원가입/로그인
- JWT 토큰 발급
- 토큰 검증
- 사용자 정보 관리

**기술:**
- FastAPI
- PostgreSQL
- JWT (jose)
- Passlib (bcrypt)

**데이터베이스:**
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

**API Endpoints:**
- POST /auth/register
- POST /auth/login
- GET /auth/me
- PUT /auth/me
- POST /auth/refresh

---

### 3. Events Service

**책임:**
- 이벤트 CRUD
- 좌석 정보 관리
- 이벤트 발행/취소
- 카테고리 관리

**기술:**
- FastAPI
- PostgreSQL
- SQLAlchemy ORM

**데이터베이스:**
```sql
CREATE TABLE events (
    event_id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    venue VARCHAR(255),
    location VARCHAR(255),
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    min_price DECIMAL(10, 2),
    max_price DECIMAL(10, 2),
    total_seats INTEGER,
    available_seats INTEGER,
    status VARCHAR(20),
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_events_category ON events(category);
CREATE INDEX idx_events_start_date ON events(start_date);
CREATE INDEX idx_events_status ON events(status);
```

---

### 4. Inventory Service (Go + gRPC)

**책임:**
- 좌석 재고 관리
- 좌석 예약 (Reserve)
- 좌석 확정 (Confirm)
- 좌석 해제 (Release)
- 분산 락을 통한 동시성 제어

**기술:**
- Go 1.21
- gRPC
- PostgreSQL
- Redis (distributed locks)

**gRPC Service:**
```protobuf
service InventoryService {
  rpc ReserveSeats(ReserveSeat Request) returns (ReserveSeatsResponse);
  rpc ConfirmReservation(ConfirmReservationRequest) returns (ConfirmReservationResponse);
  rpc ReleaseSeats(ReleaseSeatsRequest) returns (ReleaseSeatsResponse);
  rpc GetSeatStatus(GetSeatStatusRequest) returns (GetSeatStatusResponse);
}
```

**동시성 제어:**
```go
// Redis distributed lock
lock := redis.NewLock(fmt.Sprintf("seat:%s", seatID), 10*time.Second)
if err := lock.Acquire(); err != nil {
    return ErrSeatUnavailable
}
defer lock.Release()

// Update seat status
tx := db.Begin()
result := tx.Model(&Seat{}).
    Where("seat_id = ? AND status = ?", seatID, "available").
    Update("status", "reserved")
if result.RowsAffected == 0 {
    tx.Rollback()
    return ErrSeatUnavailable
}
tx.Commit()
```

---

### 5. Booking Service

**책임:**
- 예약 생성 (두 단계: Reserve → Confirm)
- 예약 조회
- 예약 취소
- 10분 TTL 관리

**기술:**
- FastAPI
- DynamoDB
- Redis (TTL tracking)
- Kafka (events)

**DynamoDB Schema:**
```json
{
  "TableName": "ticketing-bookings",
  "KeySchema": [
    {"AttributeName": "booking_id", "KeyType": "HASH"}
  ],
  "AttributeDefinitions": [
    {"AttributeName": "booking_id", "AttributeType": "S"},
    {"AttributeName": "user_id", "AttributeType": "S"},
    {"AttributeName": "event_id", "AttributeType": "S"}
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "user-index",
      "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}]
    },
    {
      "IndexName": "event-index",
      "KeySchema": [{"AttributeName": "event_id", "KeyType": "HASH"}]
    }
  ]
}
```

**예약 플로우:**
1. **Reserve**: Inventory Service 호출 → 좌석 예약
2. **Create Booking**: DynamoDB에 booking 생성 (status=reserved)
3. **Set TTL**: Redis에 10분 만료 키 설정
4. **Emit Event**: BookingCreated 이벤트 발행
5. **Wait for Payment**: 10분 내 결제 대기
6. **Confirm or Expire**: 결제 완료 시 confirmed, 시간 초과 시 cancelled

---

### 6. Payment Service

**책임:**
- Stripe PaymentIntent 생성
- 결제 상태 조회
- Webhook 처리
- 환불 처리

**기술:**
- FastAPI
- Stripe API
- Kafka (events)

**Stripe 통합:**
```python
# Create PaymentIntent
payment_intent = stripe.PaymentIntent.create(
    amount=int(total_amount * 100),  # cents
    currency="krw",
    metadata={
        "booking_id": booking_id,
        "event_id": event_id,
        "user_id": user_id
    }
)

# Webhook handling
@app.post("/payment/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    event = stripe.Webhook.construct_event(
        payload, sig_header, WEBHOOK_SECRET
    )

    if event.type == "payment_intent.succeeded":
        # Emit PaymentSucceeded event to Kafka
        await kafka_producer.send("payment-events", {
            "type": "PaymentSucceeded",
            "booking_id": event.data.object.metadata.booking_id
        })
```

---

### 7. Search Service

**책임:**
- 이벤트 전문 검색
- 자동완성
- 검색 결과 랭킹
- 인덱스 동기화

**기술:**
- FastAPI
- OpenSearch
- Kafka consumer (이벤트 동기화)

**OpenSearch 인덱스:**
```json
{
  "mappings": {
    "properties": {
      "event_id": {"type": "keyword"},
      "title": {"type": "text", "analyzer": "korean"},
      "description": {"type": "text", "analyzer": "korean"},
      "category": {"type": "keyword"},
      "venue": {"type": "text"},
      "location": {"type": "text"},
      "start_date": {"type": "date"},
      "min_price": {"type": "float"},
      "max_price": {"type": "float"},
      "available_seats": {"type": "integer"},
      "status": {"type": "keyword"}
    }
  }
}
```

**검색 쿼리:**
```python
{
  "query": {
    "bool": {
      "must": [
        {
          "multi_match": {
            "query": "BTS",
            "fields": ["title^3", "description^2", "venue"],
            "type": "best_fields",
            "fuzziness": "AUTO"
          }
        }
      ],
      "filter": [
        {"term": {"status": "published"}},
        {"term": {"category": "concert"}},
        {"range": {"min_price": {"gte": 100000}}}
      ]
    }
  }
}
```

---

### 8. Notification Service

**책임:**
- 이메일 발송 (AWS SES)
- SMS 발송 (AWS SNS)
- 푸시 알림
- 알림 템플릿 관리

**기술:**
- FastAPI
- AWS SES
- AWS SNS
- Kafka consumer

**이메일 템플릿:**
- `booking_confirmation`: 예매 확인
- `payment_success`: 결제 성공
- `booking_cancelled`: 예매 취소
- `event_reminder`: 공연 리마인더 (D-7, D-1)

---

## 데이터베이스 설계

### PostgreSQL (Auth, Events, Inventory)

**특징:**
- ACID 트랜잭션
- 복잡한 쿼리
- 관계형 데이터

**최적화:**
- B-tree 인덱스 (기본)
- Partial 인덱스 (status='published')
- Connection pooling (pgbouncer)
- Read replicas (읽기 분산)

### DynamoDB (Bookings)

**특징:**
- 높은 쓰기 처리량
- 자동 스케일링
- TTL 지원

**파티션 키 설계:**
- `booking_id` (HASH key)
- GSI: `user_id`, `event_id`

**TTL 필드:**
```json
{
  "booking_id": "book_123",
  "ttl": 1705315200  // Unix timestamp (10분 후)
}
```

### Redis (Cache, Locks, Queue)

**용도:**
1. **Distributed Locks**: 좌석 예약 동시성 제어
2. **Session Cache**: JWT 토큰 블랙리스트
3. **Rate Limiting**: API 요청 제한
4. **Virtual Waiting Room**: 대기열 관리

**Lua 스크립트 (Atomic Operations):**
```lua
-- Reserve seat with lock
local lock = redis.call('SET', KEYS[1], ARGV[1], 'NX', 'EX', 10)
if lock then
    redis.call('SET', KEYS[2], 'reserved')
    return 1
else
    return 0
end
```

---

## 이벤트 기반 아키텍처

### Kafka Topics

| Topic | Producer | Consumer | Event Types |
|-------|----------|----------|-------------|
| `booking-events` | Booking Service | Payment, Notification | BookingCreated, BookingConfirmed, BookingCancelled |
| `payment-events` | Payment Service | Booking, Notification | PaymentSucceeded, PaymentFailed, RefundProcessed |
| `event-events` | Events Service | Search, Notification | EventCreated, EventPublished, EventCancelled |
| `inventory-events` | Inventory Service | Search | SeatsReserved, SeatsConfirmed, SeatsReleased |

### Event Schema (JSON)

```json
{
  "event_id": "evt_abc123",
  "event_type": "BookingCreated",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0",
  "data": {
    "booking_id": "book_123",
    "user_id": "usr_456",
    "event_id": "evt_789",
    "seat_ids": ["A-1-3", "A-1-4"],
    "total_amount": 300000.0
  },
  "metadata": {
    "correlation_id": "corr_xyz",
    "causation_id": "cause_abc"
  }
}
```

### Saga Pattern (Choreography)

**예매 Saga:**

```
BookingService:
  1. Create Booking (status=reserved)
  2. Emit BookingCreated ───────┐
                                │
PaymentService:                 │
  3. Listen BookingCreated ◄────┘
  4. Create PaymentIntent
  5. Emit PaymentIntentCreated ─┐
                                │
User:                           │
  6. Complete Payment           │
                                │
Stripe Webhook:                 │
  7. Emit PaymentSucceeded ─────┼───┐
                                │   │
BookingService:                 │   │
  8. Listen PaymentSucceeded ◄──┼───┘
  9. Confirm Booking            │
  10. Emit BookingConfirmed ────┼───┐
                                │   │
InventoryService:               │   │
  11. Listen BookingConfirmed ◄─┼───┘
  12. Confirm Seats             │
                                │
NotificationService:            │
  13. Listen PaymentSucceeded ◄─┘
  14. Send Ticket Email
```

**보상 트랜잭션 (Failure):**

```
If Payment Fails:
  1. PaymentService → PaymentFailed Event
  2. BookingService → Cancel Booking
  3. InventoryService → Release Seats
  4. NotificationService → Send Cancellation Email
```

---

## 보안 아키텍처

### 1. 인증 & 인가

**JWT (JSON Web Token):**
```json
{
  "sub": "usr_123",
  "email": "user@example.com",
  "role": "user",
  "exp": 1705315200,
  "iat": 1705311600
}
```

**토큰 검증 플로우:**
```
Client → API Gateway
           │
           ├─→ Extract JWT from Authorization header
           ├─→ Verify signature (RS256)
           ├─→ Check expiration
           ├─→ Check blacklist (Redis)
           │
           └─→ Forward to Service (with user_id)
```

### 2. 데이터 암호화

**전송 중 (In Transit):**
- TLS 1.3
- HTTPS everywhere
- Certificate pinning (mobile)

**저장 중 (At Rest):**
- RDS: Encryption at rest (AES-256)
- DynamoDB: Server-side encryption
- S3: SSE-S3
- Secrets Manager: Automatic rotation

### 3. PCI DSS 준수

**카드 정보 처리:**
- ✅ Stripe.js (클라이언트 직접 Stripe 통신)
- ✅ 카드 정보를 서버에 저장하지 않음
- ✅ Payment Intent 방식 사용
- ✅ 3D Secure 지원

---

## 확장성 전략

### 1. Horizontal Scaling

**Auto Scaling 설정:**
```yaml
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

behavior:
  scaleUp:
    stabilizationWindowSeconds: 60
    policies:
      - type: Percent
        value: 100
        periodSeconds: 60
  scaleDown:
    stabilizationWindowSeconds: 300
    policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

### 2. Database Scaling

**Read Replicas:**
- PostgreSQL: 2-5 read replicas
- 읽기 트래픽 분산 (80% reads → replicas)

**Sharding (향후):**
- Event_id 기반 샤딩
- Consistent hashing

### 3. Caching Strategy

**Multi-Layer Cache:**
```
Client (Browser Cache: 5min)
    ↓
CloudFront (CDN: 1 day)
    ↓
Redis (Application Cache: 1 hour)
    ↓
Database
```

**캐시 패턴:**
- **Cache-Aside**: Events 목록
- **Write-Through**: 좌석 상태
- **TTL-based**: 검색 결과

---

## 고가용성 설계

### 1. Multi-AZ Deployment

모든 서비스를 최소 2개 AZ에 배포:
- **us-east-1a**: Primary
- **us-east-1b**: Secondary

### 2. Circuit Breaker

서비스 장애 격리:
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_inventory_service():
    # gRPC call to Inventory Service
    pass
```

**상태:**
- **Closed**: 정상 동작
- **Open**: 실패 임계값 초과 → 즉시 실패 반환
- **Half-Open**: 일부 요청만 시도

### 3. Health Checks

각 서비스:
```python
@app.get("/health")
async def health_check():
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "kafka": await check_kafka()
    }

    if all(checks.values()):
        return {"status": "healthy", "checks": checks}
    else:
        raise HTTPException(status_code=503, detail="Unhealthy")
```

### 4. Graceful Degradation

서비스 장애 시 기능 축소:
- Search Service 장애 → PostgreSQL fallback
- Redis 장애 → Rate limiting 비활성화
- Kafka 장애 → 동기 API 호출

---

## 기술 스택

### Backend

| Component | Technology | Version |
|-----------|-----------|---------|
| API Framework | FastAPI | 0.109.0 |
| Language | Python | 3.11 |
| Language (Inventory) | Go | 1.21 |
| ASGI Server | Uvicorn | 0.27.0 |
| Database (SQL) | PostgreSQL | 14.7 |
| Database (NoSQL) | DynamoDB | - |
| Cache | Redis | 7.0 |
| Search | OpenSearch | 2.5 |
| Message Queue | Kafka | 3.6 |
| gRPC | gRPC | 1.60 |
| ORM | SQLAlchemy | 2.0 |
| Migration | Alembic | 1.13 |

### Frontend

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | React | 18.2 |
| Language | TypeScript | 5.3 |
| Build Tool | Vite | 5.0 |
| Styling | Tailwind CSS | 3.4 |
| Routing | React Router | 6.21 |
| State (Client) | Zustand | 4.5 |
| State (Server) | React Query | 3.39 |
| Forms | React Hook Form | 7.49 |
| Validation | Zod | 3.22 |
| Payment | Stripe.js | 2.4 |
| QR Code | qrcode.react | 3.1 |

### Infrastructure

| Component | Service |
|-----------|---------|
| Cloud Provider | AWS |
| Container Orchestration | ECS Fargate |
| Load Balancer | ALB |
| CDN | CloudFront |
| Storage | S3 |
| DNS | Route 53 |
| Certificates | ACM |
| Secrets | Secrets Manager |
| Monitoring | CloudWatch |
| Tracing | X-Ray |

---

## 성능 최적화

### 1. Database Optimization

**인덱스 전략:**
```sql
-- Composite index for common queries
CREATE INDEX idx_events_category_date
ON events(category, start_date)
WHERE status = 'published';

-- Covering index (include)
CREATE INDEX idx_events_search
ON events(start_date)
INCLUDE (title, min_price, available_seats);
```

**쿼리 최적화:**
- N+1 쿼리 방지 (JOIN 사용)
- EXPLAIN ANALYZE로 실행 계획 확인
- Connection pooling (max_connections=100)

### 2. API Performance

**응답 시간 목표:**
- p50: < 100ms
- p95: < 200ms
- p99: < 500ms

**최적화 기법:**
- Async I/O (FastAPI)
- Database query optimization
- Redis caching
- Gzip compression
- CDN caching

---

**시스템 아키텍처는 지속적으로 진화합니다. 정기적인 리뷰와 개선이 필요합니다.**
