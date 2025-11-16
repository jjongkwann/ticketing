# Phase 5: Search Service & Indexing

## 📋 Overview
Implement event search and discovery using Elasticsearch. The Search Service provides full-text search, faceted filtering, and pagination. The Indexer Service watches the Events DB using the outbox pattern and indexes events to Elasticsearch.

## 🎯 Objectives
- Implement Search Service with Elasticsearch queries
- Build event indexing pipeline (CDC/Outbox pattern)
- Support full-text search, filters, and pagination
- Achieve <200ms search response time

## 👥 Agents Involved
- **data-engineer**: Elasticsearch integration and indexing pipeline

---

## 📝 Tasks

### T5.1: Implement Search Service
**Agent**: `data-engineer`
**Dependencies**: T1.2, T1.4 (Elasticsearch schema)
**Status**: ⏳ Pending

**API Endpoints**:
```python
GET /api/search?q=taylor+swift&city=Seattle&dateFrom=2025-11-01&dateTo=2025-12-31&category=CONCERT&page=0&size=20
```

**Key Features**:
- Full-text search on event name
- Filters: city, category, date range, price range
- Pagination
- Sorting by relevance, date, price
- Result caching with Redis

---

### T5.2: Implement Indexing Pipeline
**Agent**: `data-engineer`
**Dependencies**: T2.2 (Events Service), T5.1
**Status**: ⏳ Pending

**Implementation**:
- Poll `outbox_events` table every 10 seconds
- Index new/updated events to Elasticsearch
- Mark outbox events as `processed = true`
- Handle indexing failures with retry

---

## 🎯 Success Criteria
- [ ] Search returns relevant results
- [ ] Filters work correctly
- [ ] Search latency <200ms
- [ ] Events are indexed within 30 seconds

## 📊 Estimated Timeline
**2-3 days**

## 🔗 Dependencies
- **Previous**: [Phase 4: Booking & Payment](./Phase-4-Booking-Payment.md)
- **Next**: [Phase 6: Notification Service](./Phase-6-Notification.md)
