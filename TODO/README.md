# Ticketing System - Development Roadmap

> **Complete implementation guide for a production-ready ticketing system**
>
> Tech Stack: **Go** (Inventory) + **FastAPI** (Services) + **React** (Frontend)

---

## 🎯 Project Overview

This ticketing system is designed to handle high-concurrency ticket booking with **zero double-booking** guarantee. The system supports:

- ⚡ **500,000 concurrent users** during flash sales
- 🎫 **10,000+ concurrent bookings/second**
- 🔒 **Distributed locking** with Redis (Redlock)
- 🔄 **Two-phase booking**: Reservation (10 min TTL) → Payment → Confirmation
- 🔍 **Full-text search** with Elasticsearch
- 📊 **Microservices architecture** with 8+ services

---

## 📚 Phase Documentation

| Phase | Title | Agent(s) | Duration | Status |
|-------|-------|----------|----------|--------|
| **[Phase 1](./Phase-1-Architecture-Infrastructure.md)** | Architecture & Infrastructure | system-architect, devops-engineer, database-admin, data-engineer | 2-3 days | ⏳ Pending |
| **[Phase 2](./Phase-2-Auth-Events.md)** | Auth & Events Services | fullstack-developer | 3-4 days | ⏳ Pending |
| **[Phase 3](./Phase-3-Inventory-Service.md)** | Inventory Service (Go) | golang-pro | 4-5 days | ⏳ Pending |
| **[Phase 4](./Phase-4-Booking-Payment.md)** | Booking & Payment | payment-integration, fullstack-developer | 3-4 days | ⏳ Pending |
| **[Phase 5](./Phase-5-Search-Indexing.md)** | Search & Indexing | data-engineer | 2-3 days | ⏳ Pending |
| **[Phase 6](./Phase-6-Notification.md)** | Notification Service | fullstack-developer | 1-2 days | ⏳ Pending |
| **[Phase 7](./Phase-7-React-Frontend.md)** | React Frontend | frontend-developer | 5-7 days | ⏳ Pending |
| **[Phase 8](./Phase-8-Testing-QA.md)** | Testing & QA | qa-engineer, performance-engineer, security-auditor | 3-4 days | ⏳ Pending |
| **[Phase 9](./Phase-9-Documentation.md)** | Documentation & Deployment | api-documenter, docs-architect, tutorial-engineer, devops-engineer | 2-3 days | ⏳ Pending |
| **[Phase 10](./Phase-10-Final-Review.md)** | Final Review & Optimization | architect-reviewer, database-optimizer, code-reviewer | 2-3 days | ⏳ Pending |

**Total Estimated Timeline**: **27-38 days (4-6 weeks)** with parallelization



---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         API Gateway                         │
│              (Routing, Auth, Rate Limiting)                 │
└─────────────────────────────────────────────────────────────┘
         │                 │                 │
    ┌────┴────┐       ┌────┴────┐       ┌────┴────┐
    │  Auth   │       │ Events  │       │ Search  │
    │ Service │       │ Service │       │ Service │
    │(FastAPI)│       │(FastAPI)│       │(FastAPI)│
    └─────────┘       └─────────┘       └─────────┘
         │                 │                 │
         │            ┌────┴────┐       ┌────┴─────┐
         │            │Inventory│       │  ES/     │
         │            │ Service │       │OpenSearch│
         │            │  (Go)   │       └──────────┘
         │            └─────────┘
         │                 │
    ┌────┴─────────────────┴────┐
    │      Booking Service      │
    │        (FastAPI)          │
    │  (Orchestration + Saga)   │
    └────────────┬──────────────┘
                 │
            ┌────┴────┐
            │ Payment │
            │ Adapter │
            │(FastAPI)│
            └─────────┘
```

### Key Services

1. **API Gateway** (FastAPI)
   - Request routing
   - JWT validation
   - Rate limiting (100 req/min)
   - CORS configuration

2. **Auth Service** (FastAPI)
   - User registration/login
   - JWT token generation (HS256)
   - Token refresh

3. **Events Service** (FastAPI)
   - Event CRUD operations
   - Status state machine
   - Outbox pattern for indexing

4. **Inventory Service** (Go) **CRITICAL**
   - Seat availability management
   - Distributed locking with Redis
   - Optimistic locking (version numbers)
   - Reservation TTL (10 minutes)
   - Scheduled cleanup (every 1 min)

5. **Booking Service** (FastAPI)
   - Two-phase commit orchestration
   - Payment processing
   - Idempotency support (Redis)
   - Compensating transactions

6. **Payment Adapter** (FastAPI)
   - Mock payment gateway (90% success)
   - Refund support
   - Webhook simulation

7. **Search Service** (FastAPI)
   - Elasticsearch queries
   - Full-text search
   - Faceted filtering
   - Result caching

8. **Indexer Service** (FastAPI)
   - CDC from Events DB (outbox pattern)
   - Elasticsearch indexing

---

## 🗄️ Database Architecture

### 3 Separate Databases (Service Isolation)

1. **Events DB** (MySQL)
   - `events` - Event metadata
   - `outbox_events` - CDC for Search

2. **Inventory DB** (MySQL)
   - `seats` - Seat inventory with locking
   - `reservations` - Temporary holds

3. **Bookings DB** (MySQL)
   - `bookings` - Confirmed orders
   - `booking_seats` - Order line items
   - `idempotency_keys` - Duplicate prevention

### Additional Infrastructure

- **Redis**
  - Distributed locks (seat reservations)
  - Idempotency keys cache
  - Rate limiting counters
  - Search result cache

- **Elasticsearch/OpenSearch**
  - Event search index
  - Full-text + faceted search

---

## 🔄 Booking Flow (Two-Phase Commit)

```
User Action              Service              Database State
──────────────────────────────────────────────────────────────
1. Select Seats    →   Inventory Service   →  seats.status = AVAILABLE
2. Reserve Seats   →   Inventory Service   →  seats.status = RESERVED
                                               (Redis lock acquired)
                                               reservations.status = ACTIVE
                                               (expires_at = now + 10min)

3. Payment Form    →   Frontend            →  Countdown timer (10 min)

4. Submit Payment  →   Booking Service     →  Validate reservations
                   →   Payment Adapter     →  Process payment
                   →   Booking Service     →  bookings.status = CONFIRMED
                                               seats.status = BOOKED
                                               reservations.status = CONFIRMED

If payment fails:
                   →   Booking Service     →  Release reservations
                                               seats.status = AVAILABLE
                                               reservations.status = CANCELLED
```

---

## 🔐 Concurrency Control Mechanisms

### 1. Distributed Locking (Redis)
- **Lock Key**: `lock:seat:{eventId}:{seatNumber}`
- **TTL**: 30 seconds
- **Algorithm**: Simple SETNX or Redlock (for Redis Cluster)
- **Release**: Lua script (atomic check-and-delete)

### 2. Optimistic Locking (MySQL)
- **Version Column**: `seats.version` (incremented on each update)
- **Update Query**: `WHERE seat_id = ? AND version = ? AND status = 'AVAILABLE'`
- **Failure**: Concurrent modification detected → retry or fail

### 3. Reservation TTL
- **Duration**: 10 minutes
- **Cleanup**: Scheduled job (every 1 minute)
- **Expiry Check**: `reserved_until < NOW()`

---

## 🚀 Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| **Seat Availability Check** | <500ms | 99th percentile |
| **Reservation Creation** | <2s | 99th percentile |
| **Search Query** | <200ms | Elasticsearch |
| **Concurrent Bookings** | 10,000+/sec | During flash sales |
| **Concurrent Users** | 500,000 | Peak load |
| **Availability** | 99.9% | Uptime SLA |
| **Double-Booking Rate** | **0%** | **Zero tolerance** |

---

## 🛠️ Technology Stack

### Backend Services

| Service | Technology | Port | Database |
|---------|-----------|------|----------|
| API Gateway | FastAPI | 8000 | - |
| Auth Service | FastAPI | 8001 | Events DB |
| Events Service | FastAPI | 8002 | Events DB |
| **Inventory Service** | **Go** | **8003** | **Inventory DB** |
| Booking Service | FastAPI | 8004 | Bookings DB |
| Payment Adapter | FastAPI | 8005 | Bookings DB |
| Search Service | FastAPI | 8006 | Elasticsearch |
| Indexer Service | FastAPI | 8007 | Events DB |

### Frontend

- **React** 18+
- **React Router** (routing)
- **Axios** (HTTP client)
- **Context API** / **Redux** (state management)
- **TailwindCSS** / **Material-UI** (styling)

### Infrastructure

- **MySQL** 8.0 (3 separate databases)
- **Redis** 7.0 (locks, cache, rate limiting)
- **Elasticsearch** 8.0 / **OpenSearch** (search)
- **Docker** + **Docker Compose** (local development)
- **Kubernetes** (production deployment)

---

## 📋 Development Workflow

### Phase-by-Phase Approach

Each phase document contains:
- ✅ **Objectives** - What to build
- 👥 **Agents** - Which specialized agent handles the work
- 📝 **Tasks** - Detailed implementation steps
- 🎯 **Success Criteria** - How to verify completion
- 📊 **Timeline** - Estimated duration
- 🔗 **Dependencies** - Which phases must complete first

### How to Use This Roadmap

1. **Start with Phase 1**: Set up infrastructure first
2. **Follow Dependencies**: Each phase lists prerequisites
3. **Parallel Execution**: Some tasks can run concurrently (marked in docs)
4. **Track Progress**: Update status in this README
5. **Review Success Criteria**: Verify each phase before proceeding

---

## 🎯 Critical Success Factors

### 1. **Zero Double-Booking** (Phase 3)
- **Distributed locking** with Redis is mandatory
- **Optimistic locking** provides second defense
- **Lock seat numbers in sorted order** to prevent deadlocks
- **Load test** with 1000+ concurrent reservations

### 2. **Reservation Expiry** (Phase 3)
- **Cleanup job** runs every minute
- **Acquire locks** during cleanup to prevent races
- **Expired reservations** release seats back to AVAILABLE

### 3. **Idempotency** (Phase 4)
- **Client-generated** idempotency keys
- **Cache results** for 24 hours in Redis
- **Return same result** for duplicate requests

### 4. **Performance** (Phase 8)
- **<500ms** seat availability check
- **<2s** reservation creation
- **10k+ bookings/sec** sustained throughput
- **Monitor** lock acquisition time

---

## 🔍 Monitoring & Observability

### Key Metrics to Track

1. **Inventory Service** (Go)
   - Lock acquisition time (p50, p99)
   - Lock contention rate
   - Reservation expiry count
   - Cleanup job duration

2. **Booking Service**
   - Payment success rate
   - Idempotency cache hit rate
   - Booking confirmation latency
   - Rollback frequency

3. **Search Service**
   - Query latency (p50, p99)
   - Cache hit rate
   - Indexing lag

4. **System-Wide**
   - Request rate (per service)
   - Error rate (4xx, 5xx)
   - Database connection pool usage
   - Redis memory usage

---

## 📦 Deliverables

By the end of Phase 10, you will have:

- ✅ **8 microservices** (7 FastAPI + 1 Go)
- ✅ **React SPA** with complete booking flow
- ✅ **3 MySQL databases** with optimized schemas
- ✅ **Redis** for distributed locking and caching
- ✅ **Elasticsearch** for event search
- ✅ **Docker Compose** for local development
- ✅ **CI/CD pipeline** (GitHub Actions or GitLab CI)
- ✅ **Comprehensive tests** (unit, integration, E2E, load)
- ✅ **Complete documentation** (API, architecture, user guide)
- ✅ **Monitoring setup** (ELK, Prometheus, Grafana)

---

## 🚨 Risk Mitigation

### Identified Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Redis single point of failure** | High | Use Redis Sentinel or Redis Cluster |
| **Lock contention under high load** | Medium | Implement retry with exponential backoff |
| **Database deadlocks** | Medium | Always lock seats in sorted order |
| **Payment gateway timeout** | Medium | Set 30s timeout, implement retry logic |
| **Elasticsearch indexing lag** | Low | Monitor lag, alert if >60s |
| **Reservation cleanup race** | Medium | Acquire lock during cleanup |

---

## 🎓 Learning Outcomes

By completing this project, you will master:

- **Distributed Systems**: Microservices, service boundaries, data consistency
- **Concurrency Control**: Distributed locks, optimistic locking, race conditions
- **Go Programming**: High-performance REST APIs, goroutines, channels
- **FastAPI**: Async Python, dependency injection, middleware
- **React**: SPA development, state management, routing
- **Databases**: MySQL optimization, indexing, transactions
- **Redis**: Distributed locking, caching, Lua scripts
- **Elasticsearch**: Full-text search, faceted filtering, indexing
- **DevOps**: Docker, CI/CD, monitoring, logging
- **System Design**: Architecture patterns, trade-offs, scalability

---

## 📞 Support & Questions

If you encounter issues or have questions:

1. **Check the phase documentation** - Each phase has detailed instructions
2. **Review CONCEPT.md** - Original design document with detailed explanations
3. **Consult the agent** - Each phase lists the responsible specialized agent

---

## 🏁 Getting Started

Ready to build? Start with:

### [Phase 1: Architecture & Infrastructure →](./Phase-1-Architecture-Infrastructure.md)

---

<div align="center">

**Built with ❤️ using ai-orchestrator and specialized Claude Code agents**

*Zero double-booking, guaranteed.*

</div>
