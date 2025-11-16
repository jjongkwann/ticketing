# Phase 2: Core Backend Services - Part 1 (Auth & Events)

## 📋 Overview
This phase implements the foundational backend services: Authentication Service for user management and JWT tokens, Events Service for event lifecycle management, and API Gateway for routing and security.

## 🎯 Objectives
- Implement JWT-based authentication service
- Create Events Service for CRUD operations
- Build API Gateway with routing, rate limiting, and auth verification
- Establish service-to-service communication patterns

## 👥 Agents Involved
- **fullstack-developer**: FastAPI services implementation

---

## 📝 Tasks

### T2.1: Implement Auth Service with JWT
**Agent**: `fullstack-developer`
**Dependencies**: T1.2 (Docker infrastructure), T1.3 (DB schemas)
**Status**: ⏳ Pending
**Parallel**: No

**Description**:
Implement a FastAPI-based authentication service that handles user registration, login, and JWT token generation/validation.

**Technology Stack**:
- FastAPI
- Python 3.11+
- PyJWT for token generation
- bcrypt for password hashing
- MySQL (users table)

**Expected Output**:

**Project Structure**:
```
services/auth/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── user.py
│   ├── routers/
│   │   ├── __init__.py
│   │   └── auth.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── auth_service.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── jwt.py
│   │   └── password.py
│   └── config.py
├── requirements.txt
├── Dockerfile
└── README.md
```

**API Endpoints**:
```python
# POST /api/auth/register
{
  "email": "user@example.com",
  "password": "securePassword123",
  "name": "John Doe"
}
→ 201 Created
{
  "userId": "user_123",
  "email": "user@example.com",
  "name": "John Doe"
}

# POST /api/auth/login
{
  "email": "user@example.com",
  "password": "securePassword123"
}
→ 200 OK
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "tokenType": "bearer",
  "expiresIn": 3600,
  "user": {
    "userId": "user_123",
    "email": "user@example.com",
    "name": "John Doe"
  }
}

# GET /api/auth/me (requires JWT)
Authorization: Bearer <token>
→ 200 OK
{
  "userId": "user_123",
  "email": "user@example.com",
  "name": "John Doe"
}

# POST /api/auth/refresh
{
  "refreshToken": "..."
}
→ 200 OK
{
  "accessToken": "...",
  "expiresIn": 3600
}
```

**Database Schema** (add to existing):
```sql
-- Add to Events DB or create Auth DB
CREATE TABLE users (
    user_id VARCHAR(50) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_email (email)
);
```

**Key Features**:
- Password hashing with bcrypt
- JWT token generation (HS256 algorithm)
- Token expiration (1 hour for access token)
- Refresh token support (optional)
- User profile retrieval
- Input validation with Pydantic

**Configuration** (`app/config.py`):
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    class Config:
        env_file = ".env"
```

**Success Criteria**:
- [ ] User registration works with password hashing
- [ ] Login returns valid JWT token
- [ ] JWT token can be validated
- [ ] Protected endpoints require valid token
- [ ] Token expiration is enforced
- [ ] API documentation (Swagger) is available

---

### T2.2: Implement Events Service
**Agent**: `fullstack-developer`
**Dependencies**: T1.2, T1.3
**Status**: ⏳ Pending
**Parallel**: Yes (can run parallel after T2.1 completes)

**Description**:
Implement a FastAPI service for managing event lifecycle: creation, updates, status transitions, and queries.

**Technology Stack**:
- FastAPI
- Python 3.11+
- MySQL (Events DB)
- Pydantic for validation

**Expected Output**:

**Project Structure**:
```
services/events/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── event.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── event.py
│   ├── routers/
│   │   ├── __init__.py
│   │   └── events.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── event_service.py
│   └── config.py
├── requirements.txt
├── Dockerfile
└── README.md
```

**API Endpoints**:
```python
# POST /api/events (Admin only)
{
  "eventName": "Taylor Swift - Eras Tour",
  "eventDate": "2025-12-05T19:00:00Z",
  "venueName": "Lumen Field",
  "totalSeats": 50000,
  "status": "UPCOMING",
  "saleStartTime": "2025-11-01T10:00:00Z"
}
→ 201 Created
{
  "eventId": 987,
  "eventName": "Taylor Swift - Eras Tour",
  "eventDate": "2025-12-05T19:00:00Z",
  "venueName": "Lumen Field",
  "totalSeats": 50000,
  "availableSeats": 50000,
  "status": "UPCOMING",
  "saleStartTime": "2025-11-01T10:00:00Z",
  "createdAt": "2025-10-01T12:00:00Z"
}

# GET /api/events?page=0&size=20&status=ON_SALE
→ 200 OK
{
  "events": [...],
  "page": {
    "number": 0,
    "size": 20,
    "totalElements": 124,
    "totalPages": 7
  }
}

# GET /api/events/{eventId}
→ 200 OK
{
  "eventId": 987,
  "eventName": "Taylor Swift - Eras Tour",
  ...
}

# PUT /api/events/{eventId} (Admin only)
{
  "status": "ON_SALE"
}
→ 200 OK

# PUT /api/events/{eventId}/status (Admin only)
{
  "status": "SOLD_OUT"
}
→ 200 OK

# DELETE /api/events/{eventId} (Admin only)
→ 204 No Content
```

**Event Status State Machine**:
```
UPCOMING → ON_SALE → SOLD_OUT
    ↓          ↓
CANCELLED  CANCELLED
```

**Key Features**:
- Event CRUD operations
- Status transition validation
- Pagination support
- Filtering by status, date range
- Available seats tracking
- Sale window enforcement
- Outbox event publishing (for Elasticsearch indexing)

**Outbox Pattern Implementation**:
```python
# When event is created/updated, publish to outbox
async def create_event(event_data):
    # Insert event
    event = await db.insert_event(event_data)

    # Insert outbox event for indexing
    outbox_event = {
        "aggregate_id": event.event_id,
        "aggregate_type": "EVENT",
        "event_type": "EVENT_CREATED",
        "payload": event.dict(),
        "processed": False
    }
    await db.insert_outbox_event(outbox_event)

    return event
```

**Success Criteria**:
- [ ] Events can be created by admins
- [ ] Events can be queried with pagination
- [ ] Status transitions follow state machine
- [ ] Outbox events are created for indexing
- [ ] API documentation is complete

---

### T2.3: Implement API Gateway
**Agent**: `fullstack-developer`
**Dependencies**: T2.1 (Auth Service)
**Status**: ⏳ Pending
**Parallel**: Yes (can run parallel with T2.2)

**Description**:
Implement a FastAPI-based API Gateway that routes requests to backend services, validates JWT tokens, and enforces rate limiting.

**Technology Stack**:
- FastAPI
- Python 3.11+
- httpx (for service-to-service HTTP calls)
- Redis (for rate limiting)

**Expected Output**:

**Project Structure**:
```
services/gateway/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── rate_limit.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── events.py
│   │   ├── inventory.py
│   │   ├── bookings.py
│   │   └── search.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── proxy.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── jwt.py
│   └── config.py
├── requirements.txt
├── Dockerfile
└── README.md
```

**Routing Configuration**:
```python
# Service routing map
SERVICES = {
    "auth": "http://auth-service:8001",
    "events": "http://events-service:8002",
    "inventory": "http://inventory-service:8003",
    "bookings": "http://bookings-service:8004",
    "search": "http://search-service:8005"
}

# Route definitions
@app.api_route("/api/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def auth_proxy(path: str, request: Request):
    return await proxy_request(request, "auth", path)

@app.api_route("/api/events/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@require_auth  # Protected routes
async def events_proxy(path: str, request: Request):
    return await proxy_request(request, "events", path)
```

**Authentication Middleware**:
```python
from fastapi import Request, HTTPException
from functools import wraps

def require_auth(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid token")

        token = auth_header.split(" ")[1]
        user = await verify_jwt_token(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Add user info to request state
        request.state.user = user
        return await func(request, *args, **kwargs)

    return wrapper
```

**Rate Limiting Middleware**:
```python
from fastapi import Request, HTTPException
import redis
import time

redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

async def rate_limit_middleware(request: Request, call_next):
    # Get client IP or user ID
    client_id = request.client.host
    if hasattr(request.state, "user"):
        client_id = request.state.user["userId"]

    # Rate limit: 100 requests per minute
    key = f"rate_limit:{client_id}"
    current = redis_client.get(key)

    if current and int(current) >= 100:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Increment counter
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, 60)  # 1 minute window
    pipe.execute()

    response = await call_next(request)
    return response
```

**Key Features**:
- Request routing to backend services
- JWT token validation
- Rate limiting (100 req/min per user)
- Request/response logging
- CORS configuration
- Health check endpoints
- Service discovery (hardcoded for now)

**Health Check**:
```python
@app.get("/health")
async def health_check():
    # Check all backend services
    services_health = {}
    for service_name, service_url in SERVICES.items():
        try:
            response = await httpx.get(f"{service_url}/health", timeout=2.0)
            services_health[service_name] = response.status_code == 200
        except:
            services_health[service_name] = False

    all_healthy = all(services_health.values())
    status_code = 200 if all_healthy else 503

    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": services_health
    }
```

**Success Criteria**:
- [ ] Requests are correctly routed to backend services
- [ ] JWT tokens are validated on protected routes
- [ ] Rate limiting works (429 after limit)
- [ ] CORS is configured
- [ ] Health check shows service status
- [ ] API documentation is available

---

## 🎯 Phase 2 Success Criteria

- [ ] **Auth Service**: Users can register, login, and receive JWT tokens
- [ ] **Events Service**: Events can be created, queried, and status updated
- [ ] **API Gateway**: All routes are working with auth and rate limiting
- [ ] **Integration**: Services can communicate through the gateway
- [ ] **Documentation**: All APIs documented in Swagger

## 📊 Estimated Timeline
**3-4 days**

## 🔗 Dependencies
- **Previous**: [Phase 1: Architecture & Infrastructure](./Phase-1-Architecture-Infrastructure.md)
- **Next**: [Phase 3: Inventory Service (Go)](./Phase-3-Inventory-Service.md)

---

## 📌 Notes
- Auth Service uses HS256 for JWT (symmetric key). For production, consider RS256 (asymmetric).
- Events Service publishes outbox events for eventual consistency with Search.
- API Gateway is a simple proxy; for production, consider Kong, Traefik, or AWS API Gateway.
- Rate limiting is per-user; consider implementing per-endpoint limits.
- All services should have health check endpoints (`/health`).
