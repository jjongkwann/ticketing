# Phase 4: Booking & Payment Services

## 📋 Overview
This phase implements the booking orchestration and payment integration. The Booking Service coordinates the two-phase commit process (reservation → payment → confirmation) with idempotency support. The Payment Adapter provides a mock payment gateway interface.

## 🎯 Objectives
- Implement mock Payment Adapter service
- Build Booking Service with two-phase commit orchestration
- Implement idempotency mechanism to prevent duplicate bookings
- Handle payment failures with compensating transactions
- Ensure data consistency across Inventory and Bookings databases

## 👥 Agents Involved
- **payment-integration**: Payment gateway mock implementation
- **fullstack-developer**: Booking Service orchestration logic

---

## 📝 Tasks

### T4.1: Implement Mock Payment Adapter
**Agent**: `payment-integration`
**Dependencies**: T1.2 (Docker infrastructure)
**Status**: ⏳ Pending
**Parallel**: Yes (can start early)

**Description**:
Create a FastAPI service that simulates a payment gateway with success/failure responses, webhook handling, and payment status tracking.

**Technology Stack**:
- FastAPI
- Python 3.11+
- SQLAlchemy (for payment transactions)

**Expected Output**:

**Project Structure**:
```
services/payment/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── payment.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── payment.py
│   ├── routers/
│   │   ├── __init__.py
│   │   └── payment.py
│   └── config.py
├── requirements.txt
├── Dockerfile
└── README.md
```

**API Endpoints**:
```python
# POST /api/payment/process
{
  "amount": 150.00,
  "currency": "USD",
  "bookingReference": "BK-2025-001234",
  "userId": "user_123",
  "paymentMethod": {
    "type": "CREDIT_CARD",
    "cardNumber": "4111111111111111",
    "expiryMonth": 12,
    "expiryYear": 2026,
    "cvv": "123"
  }
}
→ 200 OK (90% success rate)
{
  "paymentId": "pay_abc123",
  "status": "SUCCESS",
  "amount": 150.00,
  "currency": "USD",
  "transactionId": "txn_xyz789",
  "processedAt": "2025-11-16T10:30:00Z"
}

→ 400 Bad Request (10% failure rate - simulated)
{
  "paymentId": "pay_abc124",
  "status": "FAILED",
  "errorCode": "INSUFFICIENT_FUNDS",
  "errorMessage": "Payment declined: insufficient funds"
}

# GET /api/payment/{paymentId}
→ 200 OK
{
  "paymentId": "pay_abc123",
  "status": "SUCCESS",
  "amount": 150.00,
  ...
}

# POST /api/payment/{paymentId}/refund
{
  "amount": 150.00,
  "reason": "BOOKING_CANCELLED"
}
→ 200 OK
{
  "refundId": "ref_def456",
  "status": "REFUNDED",
  "refundedAmount": 150.00
}
```

**Payment Model**:
```python
from enum import Enum
from sqlalchemy import Column, String, Float, DateTime, Enum as SQLEnum
from datetime import datetime

class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"

class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(String(50), primary_key=True)
    booking_reference = Column(String(50), nullable=False, index=True)
    user_id = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    transaction_id = Column(String(50))
    error_code = Column(String(50))
    error_message = Column(String(255))
    processed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Mock Payment Logic** (90% success rate):
```python
import random
import uuid

def process_payment(payment_request):
    # Simulate payment processing delay
    time.sleep(random.uniform(0.5, 1.5))

    # 90% success rate
    if random.random() < 0.9:
        return {
            "payment_id": f"pay_{uuid.uuid4().hex[:10]}",
            "status": "SUCCESS",
            "transaction_id": f"txn_{uuid.uuid4().hex[:10]}",
            "amount": payment_request.amount,
            "currency": payment_request.currency,
            "processed_at": datetime.utcnow()
        }
    else:
        # Simulate failure
        error_codes = ["INSUFFICIENT_FUNDS", "CARD_DECLINED", "EXPIRED_CARD"]
        error_code = random.choice(error_codes)

        return {
            "payment_id": f"pay_{uuid.uuid4().hex[:10]}",
            "status": "FAILED",
            "error_code": error_code,
            "error_message": f"Payment declined: {error_code.lower().replace('_', ' ')}",
            "amount": payment_request.amount,
            "currency": payment_request.currency
        }
```

**Success Criteria**:
- [ ] Payment processing returns success/failure
- [ ] 90% success rate is configurable
- [ ] Payment status can be queried
- [ ] Refunds are supported
- [ ] Payment IDs are unique
- [ ] API is documented

---

### T4.2: Implement Booking Service with Orchestration
**Agent**: `fullstack-developer`
**Dependencies**: T1.2, T1.3, T3.1 (Inventory Service), T4.1 (Payment)
**Status**: ⏳ Pending
**Parallel**: No

**Description**:
Build a FastAPI service that orchestrates the booking process: validates reservations, processes payments, confirms bookings, and handles failures with compensating transactions.

**Technology Stack**:
- FastAPI
- Python 3.11+
- MySQL (Bookings DB)
- httpx (for service calls)
- Redis (for idempotency)

**Expected Output**:

**Project Structure**:
```
services/booking/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── booking.py
│   │   └── booking_seat.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── booking.py
│   ├── routers/
│   │   ├── __init__.py
│   │   └── bookings.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── booking_service.py
│   │   └── idempotency_service.py
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── inventory_client.py
│   │   └── payment_client.py
│   └── config.py
├── requirements.txt
├── Dockerfile
└── README.md
```

**API Endpoints**:
```python
# POST /api/bookings/confirm
{
  "reservationIds": [1001, 1002],
  "paymentMethod": {
    "type": "CREDIT_CARD",
    "cardNumber": "4111111111111111",
    ...
  },
  "idempotencyKey": "idem_user123_20251116103000"  # Client-generated
}
→ 201 Created
{
  "bookingId": 5001,
  "bookingReference": "BK-2025-001234",
  "eventId": 987,
  "userId": "user_123",
  "seats": [
    {"seatNumber": "A1", "price": 75.00},
    {"seatNumber": "A2", "price": 75.00}
  ],
  "totalAmount": 150.00,
  "status": "CONFIRMED",
  "paymentId": "pay_abc123",
  "paymentStatus": "SUCCESS",
  "confirmedAt": "2025-11-16T10:30:00Z"
}

# If payment fails:
→ 402 Payment Required
{
  "error": "PAYMENT_FAILED",
  "message": "Payment declined: insufficient funds",
  "paymentId": "pay_abc124"
}

# If called with same idempotencyKey:
→ 200 OK (returns existing booking)

# GET /api/bookings/me (user's bookings)
Authorization: Bearer <token>
→ 200 OK
{
  "bookings": [...]
}

# GET /api/bookings/{bookingId}
→ 200 OK

# POST /api/bookings/{bookingId}/cancel
→ 200 OK
```

**Booking Service Logic** (`services/booking_service.py`):
```python
from typing import List
import httpx
from datetime import datetime

class BookingService:
    def __init__(self, db, redis_client, inventory_client, payment_client):
        self.db = db
        self.redis_client = redis_client
        self.inventory_client = inventory_client
        self.payment_client = payment_client

    async def confirm_booking(
        self,
        reservation_ids: List[int],
        payment_method: dict,
        user_id: str,
        idempotency_key: str
    ):
        # Check idempotency
        existing_booking = await self.check_idempotency(idempotency_key)
        if existing_booking:
            return existing_booking

        try:
            # Step 1: Validate reservations (call Inventory Service)
            reservations = await self.inventory_client.get_reservations(reservation_ids)

            # Validate all reservations belong to user and are active
            for res in reservations:
                if res["userId"] != user_id:
                    raise ValueError(f"Reservation {res['reservationId']} does not belong to user")
                if res["status"] != "ACTIVE":
                    raise ValueError(f"Reservation {res['reservationId']} is not active")
                if datetime.fromisoformat(res["expiresAt"]) < datetime.now():
                    raise ValueError(f"Reservation {res['reservationId']} has expired")

            # Calculate total amount
            total_amount = sum(res["seat"]["price"] for res in reservations)
            event_id = reservations[0]["eventId"]

            # Step 2: Create booking record (PENDING)
            booking = await self.create_booking(
                event_id=event_id,
                user_id=user_id,
                total_amount=total_amount,
                status="PENDING"
            )

            # Step 3: Process payment
            payment_response = await self.payment_client.process_payment(
                amount=total_amount,
                booking_reference=booking.booking_reference,
                user_id=user_id,
                payment_method=payment_method
            )

            if payment_response["status"] != "SUCCESS":
                # Payment failed - rollback
                await self.cancel_booking(booking.booking_id)
                raise PaymentFailedException(
                    payment_response.get("errorMessage", "Payment failed")
                )

            # Step 4: Update booking to CONFIRMED
            booking = await self.update_booking_status(
                booking.booking_id,
                status="CONFIRMED",
                payment_id=payment_response["paymentId"],
                payment_status="SUCCESS"
            )

            # Step 5: Create booking_seats records
            for res in reservations:
                await self.create_booking_seat(
                    booking_id=booking.booking_id,
                    seat_id=res["seat"]["seatId"],
                    price=res["seat"]["price"]
                )

            # Step 6: Notify Inventory Service to mark seats as BOOKED
            await self.inventory_client.confirm_reservations(
                reservation_ids=reservation_ids,
                booking_id=booking.booking_id
            )

            # Step 7: Store idempotency key
            await self.store_idempotency(idempotency_key, booking.booking_id)

            return booking

        except PaymentFailedException as e:
            # Compensating transaction: release reservations
            await self.inventory_client.cancel_reservations(reservation_ids)
            raise

        except Exception as e:
            # Unexpected error - try to rollback
            if booking:
                await self.cancel_booking(booking.booking_id)
            raise

    async def check_idempotency(self, idempotency_key: str):
        # Check Redis for existing booking
        booking_id = self.redis_client.get(f"idem:{idempotency_key}")
        if booking_id:
            return await self.get_booking(int(booking_id))
        return None

    async def store_idempotency(self, idempotency_key: str, booking_id: int):
        # Store for 24 hours
        self.redis_client.setex(
            f"idem:{idempotency_key}",
            86400,  # 24 hours
            str(booking_id)
        )
```

**Inventory Client** (`clients/inventory_client.py`):
```python
import httpx

class InventoryClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def get_reservations(self, reservation_ids: List[int]):
        # GET /api/inventory/reservations?ids=1,2,3
        response = await self.client.get(
            f"{self.base_url}/reservations",
            params={"ids": ",".join(map(str, reservation_ids))}
        )
        response.raise_for_status()
        return response.json()["reservations"]

    async def confirm_reservations(self, reservation_ids: List[int], booking_id: int):
        # PUT /api/inventory/reservations/confirm
        response = await self.client.put(
            f"{self.base_url}/reservations/confirm",
            json={
                "reservationIds": reservation_ids,
                "bookingId": booking_id
            }
        )
        response.raise_for_status()
        return response.json()

    async def cancel_reservations(self, reservation_ids: List[int]):
        # POST /api/inventory/reservations/cancel
        response = await self.client.post(
            f"{self.base_url}/reservations/cancel",
            json={"reservationIds": reservation_ids}
        )
        response.raise_for_status()
```

**Success Criteria**:
- [ ] Booking confirmation validates reservations
- [ ] Payments are processed successfully
- [ ] Payment failures trigger rollback
- [ ] Booking records are created
- [ ] Booking seats are linked
- [ ] Idempotency prevents duplicates
- [ ] User can query their bookings

---

### T4.3: Implement Idempotency Mechanism
**Agent**: `fullstack-developer`
**Dependencies**: T4.2
**Status**: ⏳ Pending
**Parallel**: No

**Description**:
Enhance the booking service with comprehensive idempotency support using Redis to prevent duplicate bookings from client retries.

**Expected Output**:

**Idempotency Service** (`services/idempotency_service.py`):
```python
import redis
from typing import Optional

class IdempotencyService:
    def __init__(self, redis_client: redis.Redis, ttl_seconds: int = 86400):
        self.redis = redis_client
        self.ttl = ttl_seconds  # 24 hours default

    def get_cached_result(self, idempotency_key: str) -> Optional[dict]:
        """Check if request was already processed"""
        cached = self.redis.get(f"idem:result:{idempotency_key}")
        if cached:
            return json.loads(cached)
        return None

    def cache_result(self, idempotency_key: str, result: dict):
        """Store result for future duplicate requests"""
        self.redis.setex(
            f"idem:result:{idempotency_key}",
            self.ttl,
            json.dumps(result)
        )

    def acquire_lock(self, idempotency_key: str) -> bool:
        """Acquire lock to process request (prevent concurrent duplicates)"""
        return self.redis.setnx(f"idem:lock:{idempotency_key}", "1")

    def release_lock(self, idempotency_key: str):
        """Release processing lock"""
        self.redis.delete(f"idem:lock:{idempotency_key}")
```

**Usage in Booking Handler**:
```python
@router.post("/confirm")
async def confirm_booking(
    request: BookingConfirmRequest,
    idempotency_service: IdempotencyService = Depends()
):
    # Check for cached result
    cached = idempotency_service.get_cached_result(request.idempotency_key)
    if cached:
        return JSONResponse(status_code=200, content=cached)

    # Acquire lock
    if not idempotency_service.acquire_lock(request.idempotency_key):
        raise HTTPException(status_code=409, detail="Request already processing")

    try:
        # Process booking
        result = await booking_service.confirm_booking(...)

        # Cache result
        idempotency_service.cache_result(request.idempotency_key, result)

        return result

    finally:
        idempotency_service.release_lock(request.idempotency_key)
```

**Success Criteria**:
- [ ] Duplicate requests return cached result
- [ ] Idempotency keys are required
- [ ] Results are cached for 24 hours
- [ ] Concurrent duplicate requests are blocked

---

## 🎯 Phase 4 Success Criteria

- [ ] **Payment Integration**: Mock payment gateway works reliably
- [ ] **Booking Orchestration**: Two-phase commit completes successfully
- [ ] **Failure Handling**: Payment failures trigger proper rollback
- [ ] **Idempotency**: Duplicate requests return same result
- [ ] **Data Consistency**: Bookings and seats are properly linked
- [ ] **API Documentation**: All endpoints documented

## 📊 Estimated Timeline
**3-4 days**

## 🔗 Dependencies
- **Previous**: [Phase 3: Inventory Service](./Phase-3-Inventory-Service.md)
- **Next**: [Phase 5: Search & Indexing](./Phase-5-Search-Indexing.md)

---

## 📌 Notes
- **Saga Pattern**: This implements a basic orchestration-based saga for distributed transactions.
- **Compensating Transactions**: Always release reservations if payment fails.
- **Idempotency Keys**: Clients should generate UUIDs or use `{userId}_{timestamp}`.
- **Timeout Handling**: Add timeouts for payment processing (e.g., 30 seconds).
- **Retry Logic**: Implement exponential backoff for transient failures.
- **Monitoring**: Track payment success rate, booking latency, rollback frequency.
