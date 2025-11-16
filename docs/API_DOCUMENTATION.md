# API Documentation

## Overview

Ticketing Pro는 마이크로서비스 아키텍처로 구성된 티켓 예매 시스템입니다. 모든 API는 RESTful 설계를 따르며, JSON 형식으로 데이터를 주고받습니다.

**Base URL**: `https://api.ticketing-pro.com` (프로덕션)
**Base URL**: `http://localhost:8000` (로컬 개발)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Events API](#events-api)
3. [Booking API](#booking-api)
4. [Payment API](#payment-api)
5. [Search API](#search-api)
6. [Queue API](#queue-api)
7. [Notification API](#notification-api)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)

---

## Authentication

### Overview

인증은 JWT (JSON Web Token) 방식을 사용합니다. 로그인 성공 시 발급받은 `access_token`을 모든 인증 필요 API의 헤더에 포함해야 합니다.

**Base Path**: `/api/auth`

### Headers

```
Authorization: Bearer {access_token}
Content-Type: application/json
```

---

### POST /auth/register

새로운 사용자를 등록합니다.

**Request Body**

```json
{
  "email": "user@example.com",
  "password": "securePassword123!",
  "name": "홍길동",
  "phone_number": "010-1234-5678"
}
```

**Response** (200 OK)

```json
{
  "user_id": "usr_abc123",
  "email": "user@example.com",
  "name": "홍길동",
  "phone_number": "010-1234-5678",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses**

- `400 Bad Request`: 이메일이 이미 존재
- `422 Unprocessable Entity`: 유효하지 않은 입력 값

---

### POST /auth/login

사용자 로그인을 처리합니다.

**Request Body**

```json
{
  "email": "user@example.com",
  "password": "securePassword123!"
}
```

**Response** (200 OK)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "usr_abc123",
    "email": "user@example.com",
    "name": "홍길동"
  }
}
```

**Error Responses**

- `401 Unauthorized`: 잘못된 이메일 또는 비밀번호

---

### GET /auth/me

현재 로그인한 사용자의 정보를 조회합니다.

**Headers Required**

```
Authorization: Bearer {access_token}
```

**Response** (200 OK)

```json
{
  "user_id": "usr_abc123",
  "email": "user@example.com",
  "name": "홍길동",
  "phone_number": "010-1234-5678",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses**

- `401 Unauthorized`: 토큰이 없거나 유효하지 않음

---

## Events API

이벤트(공연, 콘서트 등) 관련 API입니다.

**Base Path**: `/api/events`

---

### GET /events

이벤트 목록을 조회합니다. 페이징, 필터링, 정렬을 지원합니다.

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| page | integer | No | 페이지 번호 (기본값: 1) |
| page_size | integer | No | 페이지당 항목 수 (기본값: 20, 최대: 100) |
| category | string | No | 카테고리 필터 (concert, sports, musical, exhibition) |
| status | string | No | 상태 필터 (published, draft, cancelled) |
| min_price | float | No | 최소 가격 |
| max_price | float | No | 최대 가격 |
| start_date_from | string | No | 시작일 필터 (ISO 8601) |
| start_date_to | string | No | 종료일 필터 (ISO 8601) |
| sort_by | string | No | 정렬 기준 (start_date, price, created_at) |
| order | string | No | 정렬 순서 (asc, desc) |

**Example Request**

```
GET /api/events?category=concert&page=1&page_size=10&sort_by=start_date&order=asc
```

**Response** (200 OK)

```json
{
  "events": [
    {
      "event_id": "evt_123",
      "title": "BTS World Tour 2024",
      "description": "BTS 월드 투어 서울 공연",
      "category": "concert",
      "venue": "잠실 올림픽 주경기장",
      "location": "서울특별시 송파구",
      "start_date": "2024-06-15T19:00:00Z",
      "end_date": "2024-06-15T22:00:00Z",
      "min_price": 150000.0,
      "max_price": 500000.0,
      "total_seats": 50000,
      "available_seats": 12500,
      "status": "published",
      "image_url": "https://cdn.ticketing-pro.com/events/bts-2024.jpg",
      "created_at": "2024-01-10T09:00:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 10,
  "total_pages": 5
}
```

---

### GET /events/{event_id}

특정 이벤트의 상세 정보를 조회합니다.

**Path Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| event_id | string | Yes | 이벤트 ID |

**Response** (200 OK)

```json
{
  "event_id": "evt_123",
  "title": "BTS World Tour 2024",
  "description": "BTS 월드 투어 서울 공연...",
  "category": "concert",
  "venue": "잠실 올림픽 주경기장",
  "location": "서울특별시 송파구",
  "start_date": "2024-06-15T19:00:00Z",
  "end_date": "2024-06-15T22:00:00Z",
  "min_price": 150000.0,
  "max_price": 500000.0,
  "total_seats": 50000,
  "available_seats": 12500,
  "status": "published",
  "image_url": "https://cdn.ticketing-pro.com/events/bts-2024.jpg",
  "organizer": {
    "name": "BigHit Entertainment",
    "contact": "contact@bighit.com"
  },
  "tags": ["K-POP", "Concert", "BTS"],
  "created_at": "2024-01-10T09:00:00Z",
  "updated_at": "2024-01-12T14:30:00Z"
}
```

**Error Responses**

- `404 Not Found`: 이벤트를 찾을 수 없음

---

### GET /events/{event_id}/seats

이벤트의 좌석 정보를 조회합니다.

**Path Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| event_id | string | Yes | 이벤트 ID |

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| section | string | No | 섹션 필터 (A, B, C, VIP) |

**Response** (200 OK)

```json
{
  "event_id": "evt_123",
  "sections": [
    {
      "section": "VIP",
      "rows": [
        {
          "row": "1",
          "seats": [
            {
              "seat_id": "VIP-1-1",
              "seat_number": "1",
              "price": 500000.0,
              "status": "available"
            },
            {
              "seat_id": "VIP-1-2",
              "seat_number": "2",
              "price": 500000.0,
              "status": "sold"
            }
          ]
        }
      ]
    },
    {
      "section": "A",
      "rows": [...]
    }
  ],
  "legend": {
    "available": "예매 가능",
    "reserved": "예약 중 (10분 이내 결제 필요)",
    "sold": "판매 완료"
  }
}
```

---

### POST /events

새로운 이벤트를 생성합니다. (관리자 전용)

**Headers Required**

```
Authorization: Bearer {admin_access_token}
```

**Request Body**

```json
{
  "title": "Coldplay Live in Seoul",
  "description": "Coldplay Music of the Spheres Tour",
  "category": "concert",
  "venue": "고척 스카이돔",
  "location": "서울특별시 구로구",
  "start_date": "2024-08-20T19:00:00Z",
  "end_date": "2024-08-20T22:00:00Z",
  "min_price": 120000.0,
  "max_price": 350000.0,
  "total_seats": 25000,
  "image_url": "https://cdn.ticketing-pro.com/events/coldplay-2024.jpg"
}
```

**Response** (200 OK)

```json
{
  "event_id": "evt_456",
  "title": "Coldplay Live in Seoul",
  "status": "draft",
  "created_at": "2024-01-15T10:30:00Z",
  ...
}
```

---

## Booking API

예약 및 예매 관련 API입니다.

**Base Path**: `/api/bookings`

---

### POST /bookings

새로운 예약을 생성합니다. 예약 생성 시 좌석은 10분간 예약(reserved) 상태로 유지됩니다.

**Headers Required**

```
Authorization: Bearer {access_token}
```

**Request Body**

```json
{
  "event_id": "evt_123",
  "seat_ids": ["VIP-1-3", "VIP-1-4"],
  "total_amount": 1000000.0
}
```

**Response** (200 OK)

```json
{
  "booking_id": "book_abc123",
  "user_id": "usr_abc123",
  "event_id": "evt_123",
  "seat_ids": ["VIP-1-3", "VIP-1-4"],
  "status": "reserved",
  "total_amount": 1000000.0,
  "created_at": "2024-01-15T10:30:00Z",
  "expires_at": "2024-01-15T10:40:00Z",
  "reservation_id": "res_xyz789"
}
```

**Error Responses**

- `400 Bad Request`: 좌석이 이미 예약됨 또는 4석 초과
- `401 Unauthorized`: 인증 필요
- `404 Not Found`: 이벤트 또는 좌석을 찾을 수 없음

**Notes**

- 최대 4석까지만 예약 가능
- 예약 후 10분 이내에 결제하지 않으면 자동 취소
- 동시 예약 방지를 위해 분산 락(Redis) 사용

---

### GET /bookings/{booking_id}

예약 상세 정보를 조회합니다.

**Headers Required**

```
Authorization: Bearer {access_token}
```

**Path Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| booking_id | string | Yes | 예약 ID |

**Response** (200 OK)

```json
{
  "booking_id": "book_abc123",
  "user_id": "usr_abc123",
  "event_id": "evt_123",
  "event_title": "BTS World Tour 2024",
  "seat_ids": ["VIP-1-3", "VIP-1-4"],
  "seats": [
    {
      "seat_id": "VIP-1-3",
      "section": "VIP",
      "row": "1",
      "number": "3",
      "price": 500000.0
    },
    {
      "seat_id": "VIP-1-4",
      "section": "VIP",
      "row": "1",
      "number": "4",
      "price": 500000.0
    }
  ],
  "status": "confirmed",
  "total_amount": 1000000.0,
  "payment_intent_id": "pi_123456",
  "created_at": "2024-01-15T10:30:00Z",
  "confirmed_at": "2024-01-15T10:35:00Z"
}
```

**Error Responses**

- `401 Unauthorized`: 인증 필요 또는 권한 없음
- `404 Not Found`: 예약을 찾을 수 없음

---

### GET /bookings/user/{user_id}

특정 사용자의 모든 예약을 조회합니다.

**Headers Required**

```
Authorization: Bearer {access_token}
```

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| status | string | No | 상태 필터 (reserved, confirmed, cancelled) |
| page | integer | No | 페이지 번호 (기본값: 1) |
| page_size | integer | No | 페이지당 항목 수 (기본값: 20) |

**Response** (200 OK)

```json
{
  "bookings": [
    {
      "booking_id": "book_abc123",
      "event_id": "evt_123",
      "event_title": "BTS World Tour 2024",
      "event_date": "2024-06-15T19:00:00Z",
      "seat_count": 2,
      "status": "confirmed",
      "total_amount": 1000000.0,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20
}
```

---

### POST /bookings/{booking_id}/confirm

예약을 확정합니다. 결제 성공 후 호출됩니다.

**Headers Required**

```
Authorization: Bearer {access_token}
```

**Request Body**

```json
{
  "payment_intent_id": "pi_123456"
}
```

**Response** (200 OK)

```json
{
  "booking_id": "book_abc123",
  "status": "confirmed",
  "confirmed_at": "2024-01-15T10:35:00Z",
  "qr_code": "https://api.ticketing-pro.com/tickets/book_abc123/qr"
}
```

---

### POST /bookings/{booking_id}/cancel

예약을 취소합니다.

**Headers Required**

```
Authorization: Bearer {access_token}
```

**Response** (200 OK)

```json
{
  "booking_id": "book_abc123",
  "status": "cancelled",
  "cancelled_at": "2024-01-15T10:38:00Z",
  "refund_amount": 1000000.0,
  "refund_status": "processing"
}
```

---

## Payment API

결제 관련 API입니다. Stripe를 사용합니다.

**Base Path**: `/api/payment`

---

### POST /payment/create-intent

Stripe PaymentIntent를 생성합니다.

**Headers Required**

```
Authorization: Bearer {access_token}
```

**Request Body**

```json
{
  "booking_id": "book_abc123",
  "amount": 1000000,
  "currency": "krw",
  "metadata": {
    "event_id": "evt_123",
    "user_id": "usr_abc123"
  }
}
```

**Response** (200 OK)

```json
{
  "payment_intent_id": "pi_123456",
  "client_secret": "pi_123456_secret_abcdef",
  "amount": 1000000,
  "currency": "krw",
  "status": "requires_payment_method"
}
```

**Error Responses**

- `400 Bad Request`: 잘못된 금액 또는 통화
- `401 Unauthorized`: 인증 필요

---

### GET /payment/{payment_intent_id}

결제 상태를 조회합니다.

**Headers Required**

```
Authorization: Bearer {access_token}
```

**Response** (200 OK)

```json
{
  "payment_intent_id": "pi_123456",
  "status": "succeeded",
  "amount": 1000000,
  "currency": "krw",
  "payment_method": "card_visa_1234",
  "created_at": "2024-01-15T10:32:00Z",
  "confirmed_at": "2024-01-15T10:35:00Z"
}
```

**Payment Statuses**

- `requires_payment_method`: 결제 수단 입력 대기
- `requires_confirmation`: 결제 확인 대기
- `processing`: 결제 처리 중
- `succeeded`: 결제 성공
- `canceled`: 결제 취소
- `requires_action`: 추가 인증 필요 (3D Secure 등)

---

### POST /payment/{payment_intent_id}/cancel

결제를 취소합니다.

**Headers Required**

```
Authorization: Bearer {access_token}
```

**Response** (200 OK)

```json
{
  "payment_intent_id": "pi_123456",
  "status": "canceled",
  "canceled_at": "2024-01-15T10:37:00Z"
}
```

---

### POST /payment/webhook

Stripe webhook 이벤트를 수신합니다. (내부 사용)

**Headers Required**

```
stripe-signature: {webhook_signature}
```

**Webhook Events**

- `payment_intent.succeeded`: 결제 성공
- `payment_intent.payment_failed`: 결제 실패
- `charge.refunded`: 환불 완료

---

## Search API

이벤트 검색 API입니다. OpenSearch 기반 전문 검색을 제공합니다.

**Base Path**: `/api/search`

---

### GET /search/events

이벤트를 검색합니다.

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| q | string | Yes | 검색어 (제목, 설명, 장소) |
| category | string | No | 카테고리 필터 |
| min_price | float | No | 최소 가격 |
| max_price | float | No | 최대 가격 |
| start_date_from | string | No | 시작일 필터 |
| start_date_to | string | No | 종료일 필터 |
| location | string | No | 지역 필터 |
| page | integer | No | 페이지 번호 (기본값: 1) |
| page_size | integer | No | 페이지당 항목 수 (기본값: 20) |

**Example Request**

```
GET /api/search/events?q=BTS&category=concert&min_price=100000
```

**Response** (200 OK)

```json
{
  "results": [
    {
      "event_id": "evt_123",
      "title": "BTS World Tour 2024",
      "description": "BTS 월드 투어 서울 공연...",
      "category": "concert",
      "venue": "잠실 올림픽 주경기장",
      "location": "서울특별시 송파구",
      "start_date": "2024-06-15T19:00:00Z",
      "min_price": 150000.0,
      "max_price": 500000.0,
      "available_seats": 12500,
      "image_url": "https://cdn.ticketing-pro.com/events/bts-2024.jpg",
      "score": 15.234
    }
  ],
  "total": 23,
  "page": 1,
  "page_size": 20,
  "query": "BTS",
  "took_ms": 45
}
```

**Notes**

- 검색어는 제목(가중치 3), 설명(가중치 2), 장소(가중치 1)에서 매칭
- 결과는 관련도(score) 순으로 정렬
- Fuzzy 검색 지원 (오타 허용)

---

### GET /search/autocomplete

자동완성을 제공합니다.

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| q | string | Yes | 검색어 (최소 2자) |
| limit | integer | No | 결과 수 (기본값: 10, 최대: 20) |

**Example Request**

```
GET /api/search/autocomplete?q=BT
```

**Response** (200 OK)

```json
{
  "suggestions": [
    {
      "text": "BTS World Tour 2024",
      "event_id": "evt_123",
      "category": "concert"
    },
    {
      "text": "BTS Map of the Soul Concert",
      "event_id": "evt_456",
      "category": "concert"
    }
  ],
  "took_ms": 12
}
```

---

## Queue API

Virtual Waiting Room (대기열) API입니다.

**Base Path**: `/api/queue`

---

### POST /queue/join

대기열에 참가합니다.

**Headers Required**

```
Authorization: Bearer {access_token}
```

**Request Body**

```json
{
  "event_id": "evt_123"
}
```

**Response** (200 OK)

```json
{
  "queue_id": "queue_abc123",
  "user_id": "usr_abc123",
  "event_id": "evt_123",
  "position": 1523,
  "estimated_wait_seconds": 920,
  "joined_at": "2024-01-15T10:00:00Z",
  "status": "waiting"
}
```

---

### GET /queue/{event_id}/status

대기열 상태를 조회합니다.

**Headers Required**

```
Authorization: Bearer {access_token}
```

**Response** (200 OK)

```json
{
  "queue_id": "queue_abc123",
  "position": 1245,
  "estimated_wait_seconds": 750,
  "total_in_queue": 5000,
  "status": "waiting",
  "updated_at": "2024-01-15T10:05:00Z"
}
```

**Queue Statuses**

- `waiting`: 대기 중
- `ready`: 입장 가능 (5분 내 예매 페이지 접근 가능)
- `expired`: 시간 만료
- `completed`: 예매 완료

---

## Notification API

알림 발송 API입니다. (내부 사용)

**Base Path**: `/api/notifications`

---

### POST /notifications/email

이메일을 발송합니다.

**Request Body**

```json
{
  "to_email": "user@example.com",
  "subject": "예매 확인",
  "template": "booking_confirmation",
  "data": {
    "booking_id": "book_abc123",
    "event_title": "BTS World Tour 2024",
    "event_date": "2024-06-15T19:00:00Z"
  }
}
```

---

### POST /notifications/sms

SMS를 발송합니다.

**Request Body**

```json
{
  "phone_number": "010-1234-5678",
  "message": "예매가 완료되었습니다. 예매번호: book_abc123"
}
```

---

## Error Handling

### Error Response Format

모든 에러 응답은 다음 형식을 따릅니다:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Invalid request parameters",
    "details": {
      "field": "email",
      "issue": "Email format is invalid"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "path": "/api/auth/register"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | 성공 |
| 201 | 리소스 생성 성공 |
| 400 | 잘못된 요청 |
| 401 | 인증 실패 |
| 403 | 권한 없음 |
| 404 | 리소스를 찾을 수 없음 |
| 409 | 충돌 (이미 존재하는 리소스) |
| 422 | 유효하지 않은 엔티티 |
| 429 | Rate limit 초과 |
| 500 | 서버 오류 |
| 503 | 서비스 이용 불가 |

### Common Error Codes

| Error Code | Description |
|------------|-------------|
| `INVALID_REQUEST` | 잘못된 요청 파라미터 |
| `UNAUTHORIZED` | 인증 필요 |
| `FORBIDDEN` | 권한 없음 |
| `NOT_FOUND` | 리소스를 찾을 수 없음 |
| `ALREADY_EXISTS` | 리소스가 이미 존재 |
| `SEAT_NOT_AVAILABLE` | 좌석 예매 불가 |
| `PAYMENT_FAILED` | 결제 실패 |
| `BOOKING_EXPIRED` | 예약 시간 만료 |
| `RATE_LIMIT_EXCEEDED` | Rate limit 초과 |
| `INTERNAL_ERROR` | 내부 서버 오류 |

---

## Rate Limiting

### Limits

| Endpoint | Limit |
|----------|-------|
| POST /auth/login | 10 req/min |
| POST /auth/register | 5 req/min |
| POST /bookings | 20 req/min |
| POST /payment/create-intent | 30 req/min |
| GET /events | 100 req/min |
| GET /search/events | 60 req/min |

### Rate Limit Headers

응답 헤더에 rate limit 정보가 포함됩니다:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1705315200
```

### Rate Limit Exceeded Response

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "retry_after": 45
  }
}
```

---

## Webhook Events

### Payment Webhook Events

Stripe에서 발생하는 이벤트:

| Event | Description |
|-------|-------------|
| `payment_intent.succeeded` | 결제 성공 |
| `payment_intent.payment_failed` | 결제 실패 |
| `payment_intent.canceled` | 결제 취소 |
| `charge.refunded` | 환불 완료 |

### Booking Events (Kafka)

내부 이벤트 스트림:

| Event | Description |
|-------|-------------|
| `booking.created` | 예약 생성 |
| `booking.confirmed` | 예약 확정 |
| `booking.cancelled` | 예약 취소 |
| `booking.expired` | 예약 만료 |

---

## Versioning

API 버전은 URL 경로에 포함됩니다 (현재는 v1 생략):

```
/api/events        # v1 (현재)
/api/v2/events     # v2 (향후)
```

---

## SDK & Libraries

### JavaScript/TypeScript

```bash
npm install @ticketing-pro/api-client
```

```typescript
import { TicketingClient } from '@ticketing-pro/api-client'

const client = new TicketingClient({
  apiKey: 'your_api_key',
  baseURL: 'https://api.ticketing-pro.com'
})

const events = await client.events.list({ category: 'concert' })
```

### Python

```bash
pip install ticketing-pro
```

```python
from ticketing_pro import TicketingClient

client = TicketingClient(api_key='your_api_key')
events = client.events.list(category='concert')
```

---

## Support

- **Documentation**: https://docs.ticketing-pro.com
- **API Status**: https://status.ticketing-pro.com
- **Support Email**: api-support@ticketing-pro.com
- **GitHub**: https://github.com/ticketing-pro/api
