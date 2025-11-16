# Phase 1: Architecture & Infrastructure Setup

## 📋 Overview
This phase establishes the foundational architecture and infrastructure for the entire ticketing system. We define service boundaries, set up development environment, create database schemas, and prepare the search infrastructure.

## 🎯 Objectives
- Design complete microservices architecture
- Set up Docker Compose infrastructure for local development
- Create MySQL database schemas for all three databases (Events, Inventory, Bookings)
- Design Elasticsearch index schema for event search

## 👥 Agents Involved
- **system-architect**: Overall architecture design
- **devops-engineer**: Docker Compose and infrastructure setup
- **database-admin**: MySQL schema design and optimization
- **data-engineer**: Elasticsearch index design

---

## 📝 Tasks

### T1.1: Design System Architecture
**Agent**: `system-architect`
**Dependencies**: None
**Status**: ⏳ Pending
**Parallel**: No

**Description**:
Design the complete system architecture including microservices topology, service boundaries, communication patterns, and technology mapping.

**Input**:
- CONCEPT.md requirements
- Tech stack: Go (Inventory), FastAPI (other services), React, MySQL, Redis, Elasticsearch

**Expected Output**:
```
- Architecture diagram (system topology)
- Service boundary definitions
  - API Gateway
  - Auth Service
  - Events Service
  - Inventory Service (Go)
  - Booking Service
  - Payment Adapter
  - Search Service
  - Notification Service
  - Indexer Service
- Communication patterns (REST, async messaging)
- Technology mapping per service
- Deployment topology
- Data flow diagrams
```

**Success Criteria**:
- [ ] Clear service boundaries defined
- [ ] Technology choices justified
- [ ] Communication patterns documented
- [ ] Architecture diagram created

---

### T1.2: Create Docker Compose Infrastructure
**Agent**: `devops-engineer`
**Dependencies**: T1.1
**Status**: ⏳ Pending
**Parallel**: No

**Description**:
Set up Docker Compose configuration with all required services: MySQL (3 databases), Redis, Elasticsearch, and service containers.

**Input**:
- Architecture design from T1.1
- Service definitions

**Expected Output**:
```yaml
docker-compose.yml containing:
- MySQL (3 instances or 1 with 3 databases):
  - events_db
  - inventory_db
  - bookings_db
- Redis (for distributed locks and caching)
- Elasticsearch (for event search)
- Networks configuration
- Volume mounts for persistence
- Service containers (placeholders)
- Environment variables
- Health checks
```

**Files to Create**:
- `docker-compose.yml`
- `.env.example`
- `README.md` (setup instructions)

**Success Criteria**:
- [ ] All infrastructure services start successfully
- [ ] MySQL databases are accessible
- [ ] Redis is reachable
- [ ] Elasticsearch is running
- [ ] Health checks pass

---

### T1.3: Design and Create Database Schemas
**Agent**: `database-admin`
**Dependencies**: T1.1
**Status**: ⏳ Pending
**Parallel**: Yes (can run parallel with T1.2)

**Description**:
Create MySQL migration scripts for all three databases based on CONCEPT.md schemas, with proper indexes and constraints.

**Input**:
- Schema definitions from CONCEPT.md
- Service ownership mapping:
  - Events DB: events, event_pricing_rules, outbox_events
  - Inventory DB: seats, reservations, seat_audit
  - Bookings DB: bookings, booking_seats, idempotency_keys, payment_transactions

**Expected Output**:

**Events DB** (`migrations/events/001_initial.sql`):
```sql
-- events table
CREATE TABLE events (
    event_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    event_name VARCHAR(255) NOT NULL,
    event_date DATETIME NOT NULL,
    venue_name VARCHAR(255),
    total_seats INT NOT NULL,
    available_seats INT NOT NULL,
    status ENUM('UPCOMING', 'ON_SALE', 'SOLD_OUT', 'CANCELLED') DEFAULT 'UPCOMING',
    sale_start_time DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sale_start_time (sale_start_time),
    INDEX idx_status (status),
    INDEX idx_event_date (event_date)
);

-- outbox_events for CDC to Elasticsearch
CREATE TABLE outbox_events (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    aggregate_id BIGINT NOT NULL,
    aggregate_type VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    payload JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    INDEX idx_processed (processed),
    INDEX idx_created_at (created_at)
);
```

**Inventory DB** (`migrations/inventory/001_initial.sql`):
```sql
-- seats table
CREATE TABLE seats (
    seat_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    event_id BIGINT NOT NULL,
    seat_number VARCHAR(20) NOT NULL,
    section VARCHAR(50),
    row_number VARCHAR(10),
    seat_type ENUM('REGULAR', 'VIP', 'PREMIUM') DEFAULT 'REGULAR',
    price DECIMAL(10, 2) NOT NULL,
    status ENUM('AVAILABLE', 'RESERVED', 'BOOKED', 'BLOCKED') DEFAULT 'AVAILABLE',
    version BIGINT DEFAULT 0,  -- For optimistic locking
    reserved_by VARCHAR(50),
    reserved_until DATETIME,
    booking_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_event_seat (event_id, seat_number),
    INDEX idx_event_status (event_id, status),
    INDEX idx_reserved_until (reserved_until),
    INDEX idx_version (version)
);

-- reservations table
CREATE TABLE reservations (
    reservation_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    seat_id BIGINT NOT NULL,
    event_id BIGINT NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    session_id VARCHAR(100),
    expires_at DATETIME NOT NULL,
    status ENUM('ACTIVE', 'CONFIRMED', 'EXPIRED', 'CANCELLED') DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_seat_id (seat_id),
    INDEX idx_expires_at (expires_at),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
);
```

**Bookings DB** (`migrations/bookings/001_initial.sql`):
```sql
-- bookings table
CREATE TABLE bookings (
    booking_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    event_id BIGINT NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status ENUM('PENDING', 'CONFIRMED', 'CANCELLED', 'FAILED') DEFAULT 'PENDING',
    payment_id VARCHAR(100),
    payment_status ENUM('PENDING', 'SUCCESS', 'FAILED') DEFAULT 'PENDING',
    booking_reference VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_booking_reference (booking_reference),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- booking_seats junction table
CREATE TABLE booking_seats (
    booking_seat_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    booking_id BIGINT NOT NULL,
    seat_id BIGINT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    UNIQUE KEY uk_booking_seat (booking_id, seat_id),
    INDEX idx_seat_id (seat_id),
    INDEX idx_booking_id (booking_id)
);

-- idempotency_keys for preventing duplicate bookings
CREATE TABLE idempotency_keys (
    idempotency_key VARCHAR(100) PRIMARY KEY,
    booking_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    INDEX idx_expires_at (expires_at)
);
```

**Files to Create**:
- `migrations/events/001_initial.sql`
- `migrations/inventory/001_initial.sql`
- `migrations/bookings/001_initial.sql`
- `migrations/run_migrations.sh`

**Success Criteria**:
- [ ] All tables created successfully
- [ ] Indexes are properly defined
- [ ] Unique constraints are in place
- [ ] Migration scripts are idempotent
- [ ] Documentation includes table relationships

---

### T1.4: Design Elasticsearch Index Schema
**Agent**: `data-engineer`
**Dependencies**: T1.1
**Status**: ⏳ Pending
**Parallel**: Yes (can run parallel with T1.2, T1.3)

**Description**:
Design Elasticsearch index mapping for event search with proper analyzers, field types, and search optimization.

**Input**:
- Search requirements from CONCEPT.md
- Query patterns: keyword search, city filter, date range, category filter

**Expected Output**:

**Elasticsearch Index Mapping** (`elasticsearch/mappings/events.json`):
```json
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "analysis": {
      "analyzer": {
        "event_name_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "asciifolding"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "eventId": {
        "type": "long"
      },
      "name": {
        "type": "text",
        "analyzer": "event_name_analyzer",
        "fields": {
          "keyword": {
            "type": "keyword"
          }
        }
      },
      "city": {
        "type": "keyword"
      },
      "venue": {
        "type": "keyword"
      },
      "category": {
        "type": "keyword"
      },
      "date": {
        "type": "date",
        "format": "yyyy-MM-dd'T'HH:mm:ss'Z'"
      },
      "minPrice": {
        "type": "double"
      },
      "maxPrice": {
        "type": "double"
      },
      "availability": {
        "type": "keyword"
      },
      "availableSeats": {
        "type": "integer"
      },
      "totalSeats": {
        "type": "integer"
      },
      "description": {
        "type": "text",
        "analyzer": "event_name_analyzer"
      },
      "tags": {
        "type": "keyword"
      }
    }
  }
}
```

**Files to Create**:
- `elasticsearch/mappings/events.json`
- `elasticsearch/create_index.sh`
- `elasticsearch/README.md`

**Success Criteria**:
- [ ] Index mapping is optimized for search queries
- [ ] Text fields have proper analyzers
- [ ] Faceted search fields (city, category) are keywords
- [ ] Date range queries are supported
- [ ] Index can be created successfully

---

## 🎯 Phase 1 Success Criteria

- [ ] **Architecture**: Complete architecture diagram and service definitions
- [ ] **Infrastructure**: All services in Docker Compose are running and healthy
- [ ] **Databases**: All three MySQL databases are created with proper schemas
- [ ] **Search**: Elasticsearch index is configured and ready
- [ ] **Documentation**: Setup README with clear instructions

## 📊 Estimated Timeline
**2-3 days**

## 🔗 Next Phase
[Phase 2: Core Backend Services - Part 1 (Auth & Events)](./Phase-2-Auth-Events.md)

---

## 📌 Notes
- Database schemas follow the split by service ownership pattern (no cross-DB foreign keys)
- Elasticsearch index is designed for read-heavy search workload
- Docker Compose is for local development only; production would use Kubernetes
- All infrastructure services should have health checks configured
