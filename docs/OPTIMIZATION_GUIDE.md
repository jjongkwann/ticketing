# Performance Optimization & Best Practices Guide

## 목차

1. [성능 최적화 체크리스트](#성능-최적화-체크리스트)
2. [데이터베이스 최적화](#데이터베이스-최적화)
3. [API 성능 최적화](#api-성능-최적화)
4. [프론트엔드 최적화](#프론트엔드-최적화)
5. [캐싱 전략](#캐싱-전략)
6. [보안 강화](#보안-강화)
7. [코드 품질 개선](#코드-품질-개선)
8. [모니터링 및 알람](#모니터링-및-알람)
9. [확장성 개선](#확장성-개선)
10. [비용 최적화](#비용-최적화)

---

## 성능 최적화 체크리스트

### 백엔드 (API Services)

- [ ] **Connection Pooling 설정**
  - PostgreSQL: pgbouncer 또는 SQLAlchemy pool 설정
  - Redis: connection pool size 최적화
  - 권장: min=10, max=50

- [ ] **Query 최적화**
  - EXPLAIN ANALYZE로 슬로우 쿼리 분석
  - N+1 쿼리 제거 (eager loading 사용)
  - 인덱스 추가 (category, start_date, status 등)

- [ ] **Async I/O 활용**
  - 모든 I/O 작업을 async/await로 처리
  - httpx (동기) → httpx.AsyncClient (비동기)
  - psycopg2 → asyncpg

- [ ] **Response Compression**
  - GZip middleware 활성화
  - 최소 크기: 500 bytes

- [ ] **Pagination 구현**
  - 모든 목록 API에 page/page_size 파라미터
  - 기본값: page_size=20, max=100

### 프론트엔드

- [ ] **Code Splitting**
  - React.lazy() for route-based splitting
  - Dynamic imports for heavy components

- [ ] **Asset Optimization**
  - 이미지 압축 (WebP, AVIF)
  - SVG 최적화
  - Font subsetting

- [ ] **Bundle Size Reduction**
  - Tree shaking 활성화
  - 불필요한 dependencies 제거
  - moment.js → date-fns (87% smaller)

- [ ] **Caching Strategy**
  - Service Worker for offline support
  - HTTP caching headers
  - LocalStorage for user preferences

### 인프라

- [ ] **CDN 설정**
  - CloudFront for static assets
  - Cache-Control headers
  - Gzip/Brotli compression

- [ ] **Auto Scaling**
  - ECS 서비스별 auto scaling 규칙
  - Target tracking policies (CPU 70%, Memory 80%)

- [ ] **Load Balancing**
  - ALB health checks (30s interval)
  - Connection draining (60s)

---

## 데이터베이스 최적화

### 1. 인덱스 전략

**현재 상태 분석:**
```sql
-- 인덱스 사용률 확인
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY schemaname, tablename;
```

**추천 인덱스:**

```sql
-- Events Service
CREATE INDEX CONCURRENTLY idx_events_category_date
ON events(category, start_date)
WHERE status = 'published';

CREATE INDEX CONCURRENTLY idx_events_available_seats
ON events(available_seats)
WHERE available_seats > 0;

-- Composite index for search
CREATE INDEX CONCURRENTLY idx_events_search
ON events USING GIN(to_tsvector('korean', title || ' ' || description));

-- Auth Service
CREATE INDEX CONCURRENTLY idx_users_email_lower
ON users(LOWER(email));

-- Covering index (avoid table access)
CREATE INDEX CONCURRENTLY idx_events_list
ON events(start_date DESC)
INCLUDE (title, category, min_price, available_seats, image_url)
WHERE status = 'published';
```

### 2. 쿼리 최적화

**Before (N+1 Query):**
```python
# Bad: N+1 queries
events = db.query(Event).filter(Event.status == 'published').all()
for event in events:
    bookings = db.query(Booking).filter(Booking.event_id == event.event_id).all()
    event.booking_count = len(bookings)
```

**After (JOIN):**
```python
# Good: Single query with JOIN
from sqlalchemy import func

events = db.query(
    Event,
    func.count(Booking.booking_id).label('booking_count')
).join(
    Booking, Event.event_id == Booking.event_id, isouter=True
).filter(
    Event.status == 'published'
).group_by(
    Event.event_id
).all()
```

### 3. Connection Pooling

**SQLAlchemy 설정:**
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,           # 최소 연결 수
    max_overflow=10,        # 추가 연결 수
    pool_timeout=30,        # 연결 대기 시간
    pool_recycle=3600,      # 1시간마다 연결 재사용
    pool_pre_ping=True,     # 연결 health check
    echo=False,             # SQL 로깅 off (프로덕션)
)
```

### 4. 파티셔닝 (대용량 데이터)

**Bookings 테이블 월별 파티셔닝:**
```sql
-- 메인 테이블 (파티션 키: created_at)
CREATE TABLE bookings_partitioned (
    booking_id UUID,
    user_id UUID,
    event_id UUID,
    created_at TIMESTAMP,
    ...
) PARTITION BY RANGE (created_at);

-- 월별 파티션 생성
CREATE TABLE bookings_2024_01 PARTITION OF bookings_partitioned
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE bookings_2024_02 PARTITION OF bookings_partitioned
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

### 5. VACUUM 및 ANALYZE

**정기 실행 (cron):**
```bash
# 매일 03:00 실행
0 3 * * * psql -h $DB_HOST -U $DB_USER -d ticketing_events -c "VACUUM ANALYZE events;"
0 3 * * * psql -h $DB_HOST -U $DB_USER -d ticketing_auth -c "VACUUM ANALYZE users;"
```

---

## API 성능 최적화

### 1. Async/Await 전환

**Before (Synchronous):**
```python
import requests

@app.get("/events/{event_id}")
def get_event(event_id: str):
    event = db.query(Event).filter(Event.event_id == event_id).first()

    # Blocking I/O
    availability = requests.get(f"http://inventory:8001/seats/{event_id}")

    return {"event": event, "availability": availability.json()}
```

**After (Asynchronous):**
```python
import httpx

@app.get("/events/{event_id}")
async def get_event(event_id: str):
    event = await db_async.execute(
        select(Event).filter(Event.event_id == event_id)
    )

    # Non-blocking I/O
    async with httpx.AsyncClient() as client:
        availability = await client.get(f"http://inventory:8001/seats/{event_id}")

    return {"event": event, "availability": availability.json()}
```

### 2. Response Compression

**Middleware 추가:**
```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=500)
```

### 3. Response Caching

**Redis 캐싱:**
```python
import json
from redis import Redis

redis_client = Redis(host='redis', port=6379, decode_responses=True)

@app.get("/events")
async def get_events(category: str = None):
    # Cache key
    cache_key = f"events:list:{category or 'all'}"

    # Check cache
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Query database
    events = await db.query(Event).filter(...).all()

    # Set cache (TTL: 5 minutes)
    redis_client.setex(cache_key, 300, json.dumps(events))

    return events
```

### 4. Batch API

**여러 요청을 한 번에:**
```python
@app.post("/batch")
async def batch_request(requests: List[BatchRequest]):
    """
    요청 예시:
    [
      {"method": "GET", "path": "/events/evt_123"},
      {"method": "GET", "path": "/bookings/book_456"}
    ]
    """
    results = []

    for req in requests:
        # Process each request
        result = await process_request(req)
        results.append(result)

    return {"results": results}
```

### 5. Rate Limiting 최적화

**Sliding Window Counter (Redis):**
```python
import time
from redis import Redis

redis = Redis()

def rate_limit(user_id: str, limit: int = 100, window: int = 60):
    """
    Sliding window rate limiter
    limit: 최대 요청 수
    window: 시간 윈도우 (초)
    """
    key = f"ratelimit:{user_id}"
    now = time.time()

    # Remove old entries
    redis.zremrangebyscore(key, 0, now - window)

    # Count requests in current window
    count = redis.zcard(key)

    if count >= limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Add current request
    redis.zadd(key, {now: now})
    redis.expire(key, window)
```

---

## 프론트엔드 최적화

### 1. Code Splitting

**Route-based Splitting:**
```typescript
// App.tsx
import { lazy, Suspense } from 'react'

const HomePage = lazy(() => import('./pages/HomePage'))
const EventDetailPage = lazy(() => import('./pages/EventDetailPage'))
const CheckoutPage = lazy(() => import('./pages/CheckoutPage'))

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/events/:id" element={<EventDetailPage />} />
        <Route path="/checkout/:id" element={<CheckoutPage />} />
      </Routes>
    </Suspense>
  )
}
```

**Component-based Splitting:**
```typescript
// Heavy component
const SeatSelection = lazy(() => import('./components/SeatSelection'))

function EventDetailPage() {
  return (
    <div>
      <EventInfo />
      <Suspense fallback={<SeatSelectionSkeleton />}>
        <SeatSelection />
      </Suspense>
    </div>
  )
}
```

### 2. 이미지 최적화

**Vite Image Plugin:**
```bash
npm install vite-plugin-imagemin
```

```typescript
// vite.config.ts
import imagemin from 'vite-plugin-imagemin'

export default defineConfig({
  plugins: [
    imagemin({
      gifsicle: {
        optimizationLevel: 7,
        interlaced: false
      },
      optipng: {
        optimizationLevel: 7
      },
      mozjpeg: {
        quality: 80
      },
      pngquant: {
        quality: [0.8, 0.9],
        speed: 4
      },
      svgo: {
        plugins: [
          {
            name: 'removeViewBox'
          },
          {
            name: 'removeEmptyAttrs',
            active: false
          }
        ]
      }
    })
  ]
})
```

**Lazy Loading Images:**
```typescript
function EventCard({ event }) {
  return (
    <div>
      <img
        src={event.image_url}
        loading="lazy"  // Native lazy loading
        decoding="async"
        alt={event.title}
      />
    </div>
  )
}
```

### 3. React Query 최적화

**Stale Time 설정:**
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5분 동안 fresh
      cacheTime: 10 * 60 * 1000,     // 10분 동안 캐시 유지
      refetchOnWindowFocus: false,   // 포커스 시 refetch 안 함
      retry: 2,                      // 실패 시 2번 재시도
    }
  }
})
```

**Prefetching:**
```typescript
function EventsList() {
  const queryClient = useQueryClient()

  const { data: events } = useQuery(['events'], fetchEvents)

  // Prefetch event details on hover
  const handleMouseEnter = (eventId: string) => {
    queryClient.prefetchQuery(
      ['event', eventId],
      () => fetchEventDetail(eventId)
    )
  }

  return events.map(event => (
    <EventCard
      key={event.id}
      event={event}
      onMouseEnter={() => handleMouseEnter(event.id)}
    />
  ))
}
```

### 4. Virtual Scrolling

**대량 데이터 렌더링:**
```bash
npm install react-window
```

```typescript
import { FixedSizeList } from 'react-window'

function EventsList({ events }) {
  const Row = ({ index, style }) => (
    <div style={style}>
      <EventCard event={events[index]} />
    </div>
  )

  return (
    <FixedSizeList
      height={600}
      itemCount={events.length}
      itemSize={200}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  )
}
```

### 5. Bundle 분석

```bash
# Bundle 크기 분석
npm run build
npx vite-bundle-visualizer
```

**큰 dependencies 제거:**
- moment.js (289KB) → date-fns (18KB)
- lodash (71KB) → lodash-es (tree-shakeable)

---

## 캐싱 전략

### 1. Multi-Layer Caching

```
Browser Cache (1 hour)
    ↓
CloudFront (1 day)
    ↓
Redis (5 minutes)
    ↓
Database
```

### 2. Cache-Control Headers

**Static Assets:**
```nginx
# CloudFront에서 설정
location ~* \.(js|css|png|jpg|jpeg|gif|svg|woff|woff2)$ {
    add_header Cache-Control "public, max-age=31536000, immutable";
}
```

**API Responses:**
```python
from fastapi.responses import JSONResponse

@app.get("/events")
async def get_events():
    events = await fetch_events()

    return JSONResponse(
        content=events,
        headers={
            "Cache-Control": "public, max-age=300",  # 5분
            "ETag": generate_etag(events)
        }
    )
```

### 3. Redis 캐시 패턴

**Cache-Aside (Lazy Loading):**
```python
async def get_event(event_id: str):
    # Try cache first
    cached = await redis.get(f"event:{event_id}")
    if cached:
        return json.loads(cached)

    # Cache miss: query DB
    event = await db.query(Event).filter(Event.event_id == event_id).first()

    # Update cache
    await redis.setex(f"event:{event_id}", 300, json.dumps(event))

    return event
```

**Write-Through:**
```python
async def update_event(event_id: str, data: dict):
    # Update database
    await db.query(Event).filter(Event.event_id == event_id).update(data)
    await db.commit()

    # Update cache immediately
    event = await db.query(Event).filter(Event.event_id == event_id).first()
    await redis.setex(f"event:{event_id}", 300, json.dumps(event))
```

**Cache Invalidation:**
```python
# Event updated → invalidate related caches
async def on_event_updated(event_id: str):
    await redis.delete(f"event:{event_id}")
    await redis.delete("events:list:*")  # Pattern delete
    await redis.delete(f"seats:{event_id}")
```

---

## 보안 강화

### 1. OWASP Top 10 대응

**SQL Injection 방지:**
```python
# Bad
query = f"SELECT * FROM users WHERE email = '{email}'"  # 위험!

# Good
from sqlalchemy import text
query = text("SELECT * FROM users WHERE email = :email")
result = await db.execute(query, {"email": email})
```

**XSS 방지:**
```typescript
// React는 기본적으로 XSS 방지
// 단, dangerouslySetInnerHTML 사용 시 주의
function EventDescription({ html }) {
  // Bad
  return <div dangerouslySetInnerHTML={{ __html: html }} />

  // Good: DOMPurify 사용
  import DOMPurify from 'dompurify'
  const clean = DOMPurify.sanitize(html)
  return <div dangerouslySetInnerHTML={{ __html: clean }} />
}
```

**CSRF 방지:**
```python
from fastapi_csrf_protect import CsrfProtect

@app.post("/bookings")
async def create_booking(
    csrf_protect: CsrfProtect = Depends()
):
    await csrf_protect.validate_csrf()
    # ... booking logic
```

### 2. Rate Limiting 강화

**IP-based + User-based:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/auth/login")
@limiter.limit("5/minute")  # IP 기준
async def login(request: Request, user: LoginRequest):
    # 추가 user-based rate limit
    user_limit_key = f"login:{user.email}"
    if not await check_user_rate_limit(user_limit_key):
        raise HTTPException(429, "Too many login attempts")

    # ... login logic
```

### 3. Secrets Management

**환경 변수 암호화:**
```python
# Bad
DATABASE_URL = "postgresql://admin:password@host/db"  # 위험!

# Good: AWS Secrets Manager
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

db_creds = get_secret('ticketing/database')
DATABASE_URL = f"postgresql://{db_creds['username']}:{db_creds['password']}@{db_creds['host']}/{db_creds['database']}"
```

---

## 코드 품질 개선

### 1. Type Hints (Python)

```python
from typing import List, Optional
from pydantic import BaseModel

class Event(BaseModel):
    event_id: str
    title: str
    category: str
    start_date: datetime
    available_seats: int

async def get_events(
    category: Optional[str] = None,
    limit: int = 20
) -> List[Event]:
    """
    Get list of events

    Args:
        category: Filter by category
        limit: Maximum number of results

    Returns:
        List of Event objects
    """
    # ... implementation
```

### 2. Error Handling

**통일된 에러 응답:**
```python
from fastapi import HTTPException
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            message=str(exc),
            details={"path": request.url.path}
        ).dict()
    )
```

### 3. Logging

**구조화된 로깅:**
```python
import structlog

logger = structlog.get_logger()

@app.post("/bookings")
async def create_booking(booking: BookingRequest):
    logger.info(
        "booking_attempt",
        user_id=booking.user_id,
        event_id=booking.event_id,
        seat_count=len(booking.seat_ids)
    )

    try:
        result = await process_booking(booking)
        logger.info("booking_success", booking_id=result.booking_id)
        return result
    except Exception as e:
        logger.error(
            "booking_failed",
            error=str(e),
            user_id=booking.user_id
        )
        raise
```

---

## 모니터링 및 알람

### 1. CloudWatch Custom Metrics

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def record_booking_metric(success: bool, latency_ms: float):
    cloudwatch.put_metric_data(
        Namespace='Ticketing/Bookings',
        MetricData=[
            {
                'MetricName': 'BookingAttempts',
                'Value': 1.0,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'Status', 'Value': 'success' if success else 'failure'}
                ]
            },
            {
                'MetricName': 'BookingLatency',
                'Value': latency_ms,
                'Unit': 'Milliseconds'
            }
        ]
    )
```

### 2. 주요 메트릭

**Application Metrics:**
- Request rate (req/s)
- Error rate (%)
- Latency (p50, p95, p99)
- Active users
- Booking success rate

**Infrastructure Metrics:**
- CPU utilization
- Memory usage
- Network I/O
- Disk I/O
- Database connections

### 3. 알람 설정

**Critical Alarms:**
```yaml
HighErrorRate:
  metric: HTTPCode_Target_5XX_Count
  threshold: 10 errors in 5 minutes
  action: SNS notification → PagerDuty

HighLatency:
  metric: TargetResponseTime
  threshold: p95 > 500ms
  action: SNS notification

LowAvailableSeats:
  metric: CustomMetric:AvailableSeats
  threshold: < 100 seats for popular event
  action: Trigger auto-scaling
```

---

## 확장성 개선

### 1. 수평 확장 (Horizontal Scaling)

**Stateless 서비스:**
- 모든 상태를 외부 저장소에 (Redis, DynamoDB)
- Session을 JWT로 대체

**Auto Scaling Policy:**
```json
{
  "TargetValue": 70.0,
  "PredefinedMetricType": "ECSServiceAverageCPUUtilization",
  "ScaleInCooldown": 300,
  "ScaleOutCooldown": 60
}
```

### 2. Database Read Replicas

**읽기 분산:**
```python
from sqlalchemy import create_engine

# Master (write)
engine_master = create_engine(MASTER_URL)

# Replica (read)
engine_replica = create_engine(REPLICA_URL)

# Read from replica
async def get_events():
    async with engine_replica.connect() as conn:
        result = await conn.execute(select(Event))
        return result.all()

# Write to master
async def create_event(event: Event):
    async with engine_master.connect() as conn:
        await conn.execute(insert(Event).values(**event.dict()))
```

### 3. CDN Edge Caching

**Lambda@Edge for dynamic content:**
```javascript
// CloudFront Function
function handler(event) {
    var request = event.request;
    var uri = request.uri;

    // Add index.html for SPA routing
    if (uri.endsWith('/')) {
        request.uri += 'index.html';
    } else if (!uri.includes('.')) {
        request.uri = '/index.html';
    }

    return request;
}
```

---

## 비용 최적화

### 1. AWS Cost Reduction

**Reserved Instances:**
- RDS: 1년 예약 (40% 절감)
- ElastiCache: 1년 예약 (35% 절감)

**Spot Instances:**
- ECS Fargate Spot (70% 절감)
- 권장 비율: On-Demand 20% / Spot 80%

**S3 Lifecycle:**
```json
{
  "Rules": [
    {
      "Id": "ArchiveOldLogs",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ],
      "Expiration": {
        "Days": 365
      }
    }
  ]
}
```

### 2. 불필요한 리소스 제거

**Unused Resources:**
- Unattached EBS volumes
- Unused Elastic IPs
- Old AMI snapshots
- Orphaned CloudWatch Logs

**Scheduled Scaling:**
```bash
# Dev/Staging 환경: 업무 시간 외 scale down
0 20 * * * aws ecs update-service --cluster dev --service api-gateway --desired-count 0
0 9 * * * aws ecs update-service --cluster dev --service api-gateway --desired-count 2
```

---

## 결론

### 우선순위별 실행 계획

**Phase 1 (즉시 적용):**
1. Database 인덱스 추가
2. Connection pooling 설정
3. Response compression 활성화
4. CloudWatch 알람 설정

**Phase 2 (1-2주 내):**
1. Redis 캐싱 구현
2. Code splitting 적용
3. Image optimization
4. Auto scaling 정책 최적화

**Phase 3 (1개월 내):**
1. Async I/O 전환
2. Read replicas 구성
3. CDN 캐싱 전략 구현
4. 비용 최적화 (Reserved Instances)

**Phase 4 (지속적):**
1. 성능 모니터링 및 분석
2. 슬로우 쿼리 최적화
3. 보안 취약점 스캔
4. 정기 부하 테스트

---

**지속적인 모니터링과 개선이 시스템 성능의 핵심입니다!**
