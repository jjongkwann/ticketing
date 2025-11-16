# Ticketmaster Pro 급 엔터프라이즈 기능 명세

## 1. 대기열 시스템 (Virtual Waiting Room)

### 1.1 개요
대규모 티켓 오픈 시 서버 과부하를 방지하고 공정한 구매 기회를 제공하는 가상 대기실 시스템

### 1.2 핵심 기능

#### Queue 시스템 구조
```
[사용자 접속]
    ↓
[대기실 진입] - Queue Position 할당
    ↓
[실시간 대기 순번 표시]
    ↓
[순번 도달] - Token 발급 (15분 유효)
    ↓
[티켓 구매 페이지 접근]
```

#### 기술 구현
- **Redis Sorted Set**: 타임스탬프 기반 대기열 관리
- **WebSocket**: 실시간 대기 순번 업데이트
- **JWT Token**: 구매 권한 인증 (15분 TTL)
- **Rate Limiting**: IP당 접속 제한

```python
# Redis Queue 구조 예시
ZADD waiting_room:event_123 {timestamp} {user_id}
ZRANK waiting_room:event_123 {user_id}  # 현재 순위 조회
```

#### UI/UX 요구사항
```
┌─────────────────────────────────────────┐
│        🎫 티켓 오픈 대기 중              │
├─────────────────────────────────────────┤
│                                         │
│         현재 대기 인원                   │
│            12,458명                     │
│                                         │
│         내 순번                          │
│            #1,234                       │
│                                         │
│    ███████████░░░░░░░░░░ 45%           │
│                                         │
│    예상 대기 시간: 약 8분                │
│                                         │
│    ⚠️ 이 창을 닫지 마세요                │
│    순번이 되면 자동으로 이동됩니다        │
│                                         │
└─────────────────────────────────────────┘
```

---

## 2. Dynamic Pricing (다이나믹 프라이싱)

### 2.1 개요
수요-공급에 따라 실시간으로 티켓 가격을 조정하는 시스템

### 2.2 가격 결정 요소
- **잔여 좌석 수**: 매진 임박 시 가격 상승
- **구매 속도**: 빠른 판매 시 가격 상승
- **시간대**: 공연 임박 시 가격 변동
- **과거 데이터**: ML 모델 기반 수요 예측

### 2.3 가격 변동 알고리즘
```python
def calculate_dynamic_price(base_price, remaining_seats, total_seats, time_to_event):
    occupancy_rate = (total_seats - remaining_seats) / total_seats

    # 좌석 점유율에 따른 배수
    if occupancy_rate > 0.9:  # 90% 이상 판매
        multiplier = 1.5
    elif occupancy_rate > 0.7:  # 70% 이상
        multiplier = 1.3
    elif occupancy_rate > 0.5:  # 50% 이상
        multiplier = 1.1
    else:
        multiplier = 1.0

    # 공연 임박도에 따른 조정
    days_to_event = time_to_event.days
    if days_to_event < 7:
        multiplier *= 1.2
    elif days_to_event < 14:
        multiplier *= 1.1

    return base_price * multiplier
```

### 2.4 UI 표시
```
┌─────────────────────────────────────┐
│ VIP석                               │
│ ₩150,000 → ₩195,000 ⬆️ (+30%)      │
│ 🔥 인기로 인해 가격이 상승했습니다   │
│                                     │
│ [가격 변동 그래프 보기]              │
└─────────────────────────────────────┘
```

---

## 3. Verified Fan (팬 인증 시스템)

### 3.1 개요
리셀러 방지 및 진성 팬에게 우선 구매 기회를 제공하는 시스템

### 3.2 인증 프로세스
1. **사전 등록**
   - 이메일, 전화번호 인증
   - SNS 연동 (선택)
   - 간단한 퀴즈 (아티스트 관련)

2. **팬 스코어 산정**
   - 과거 구매 이력: 30%
   - SNS 활동: 20%
   - 커뮤니티 참여: 20%
   - 사전 등록 시기: 10%
   - 퀴즈 정답률: 20%

3. **등급 부여**
   - **Platinum**: 90점 이상 → 우선 구매 (티켓 오픈 1시간 전)
   - **Gold**: 70-89점 → 우선 구매 (티켓 오픈 30분 전)
   - **Silver**: 50-69점 → 일반 구매
   - **Bronze**: 50점 미만 → 일반 구매 (제한적)

### 3.3 데이터베이스 스키마
```sql
CREATE TABLE verified_fans (
    user_id VARCHAR(50) PRIMARY KEY,
    event_id VARCHAR(50),
    fan_score INT,
    tier VARCHAR(20),
    verified_at TIMESTAMP,
    quiz_score INT,
    past_purchases INT,
    social_engagement_score INT,
    early_access_granted BOOLEAN
);
```

### 3.4 UI 표시
```
┌─────────────────────────────────────────┐
│  ✅ Verified Fan 인증 완료               │
│                                         │
│  등급: 🥇 Gold (82점)                    │
│                                         │
│  혜택:                                   │
│  • 티켓 오픈 30분 전 우선 구매           │
│  • 최대 4매 구매 가능                    │
│  • 리셀 방지 보호                        │
│                                         │
│  우선 구매 시작: 2024.03.15 09:30       │
│                                         │
└─────────────────────────────────────────┘
```

---

## 4. SafeTix (안전 티켓 시스템)

### 4.1 개요
위조 방지 및 안전한 티켓 전송을 위한 동적 QR 코드 시스템

### 4.2 핵심 기술
- **Rotating QR Code**: 60초마다 갱신되는 동적 QR
- **NFC 통합**: 모바일 NFC 태그 지원
- **블록체인 검증**: 티켓 소유권 추적
- **얼굴 인식**: (선택) 본인 확인

### 4.3 QR 코드 생성 알고리즘
```python
import time
import hashlib
import hmac

def generate_safe_ticket_qr(booking_id, secret_key):
    timestamp = int(time.time() / 60)  # 1분 단위
    message = f"{booking_id}:{timestamp}"
    signature = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    qr_data = f"{booking_id}:{timestamp}:{signature}"
    return qr_data

# 검증
def verify_safe_ticket(qr_data, secret_key):
    booking_id, timestamp, signature = qr_data.split(':')
    current_time = int(time.time() / 60)

    # 2분 이내의 QR만 유효
    if abs(current_time - int(timestamp)) > 2:
        return False

    expected_sig = hmac.new(
        secret_key.encode(),
        f"{booking_id}:{timestamp}".encode(),
        hashlib.sha256
    ).hexdigest()

    return signature == expected_sig
```

### 4.4 UI 표시
```
┌─────────────────────────────────────┐
│          SafeTix                    │
│                                     │
│     [Rotating QR Code]              │
│     (60초마다 자동 갱신)             │
│                                     │
│  🔒 이 QR 코드는 60초마다 변경되어  │
│     위조를 방지합니다                │
│                                     │
│  예약번호: BK-2024052012345         │
│  유효기간: 2024.05.20 17:00-22:00   │
│                                     │
│  [Apple Wallet에 추가]              │
│  [Google Pay에 추가]                │
│                                     │
└─────────────────────────────────────┘
```

---

## 5. Official Platinum (공식 리셀 마켓)

### 5.1 개요
공식적으로 인정된 티켓 재판매 플랫폼 (수수료 수익 모델)

### 5.2 핵심 기능
- **가격 상한선**: 원가의 150% 이하
- **판매자 인증**: 본인 확인 필수
- **구매자 보호**: 환불 보장
- **수수료**: 판매가의 10% (판매자 부담) + 5% (구매자 부담)

### 5.3 재판매 프로세스
```
[판매자]
    ↓ 티켓 등록
[시스템 검증] - SafeTix 소유권 확인
    ↓
[마켓에 등록] - 가격 상한선 체크
    ↓
[구매자 구매]
    ↓
[티켓 소유권 이전] - 블록체인 기록
    ↓
[수수료 정산]
```

### 5.4 데이터베이스 스키마
```sql
CREATE TABLE resale_listings (
    listing_id VARCHAR(50) PRIMARY KEY,
    booking_id VARCHAR(50),
    seller_id VARCHAR(50),
    original_price DECIMAL(10,2),
    listing_price DECIMAL(10,2),
    max_price DECIMAL(10,2),  -- 원가의 150%
    status VARCHAR(20),  -- active, sold, cancelled
    created_at TIMESTAMP,
    sold_at TIMESTAMP,
    buyer_id VARCHAR(50),
    seller_fee DECIMAL(10,2),
    buyer_fee DECIMAL(10,2)
);
```

### 5.5 UI 표시
```
┌─────────────────────────────────────────┐
│  Official Platinum 리셀 마켓            │
├─────────────────────────────────────────┤
│                                         │
│  원래 가격: ₩150,000                     │
│  판매 가격: ₩180,000                     │
│  구매자 수수료: ₩9,000 (5%)              │
│  ─────────────────────                  │
│  총 결제 금액: ₩189,000                  │
│                                         │
│  ✅ 공식 인증된 안전한 거래               │
│  ✅ 티켓 진위 보장                       │
│  ✅ 100% 환불 보장                       │
│                                         │
│  판매자: user_****789 (신뢰도 98%)      │
│  등록일: 2024.03.10                     │
│                                         │
│          [안전하게 구매하기]             │
│                                         │
└─────────────────────────────────────────┘
```

---

## 6. Seat Geek 통합 (좌석 시각화)

### 6.1 3D 좌석 뷰
- **360도 회전**: 모든 각도에서 무대 시야 확인
- **실제 사진**: 각 구역에서 촬영한 실제 뷰
- **AR 프리뷰**: 스마트폰으로 AR 시뮬레이션

### 6.2 구현 기술
- **Three.js**: 3D 렌더링
- **WebGL**: GPU 가속
- **AR.js**: 증강 현실

### 6.3 UI 구성
```
┌─────────────────────────────────────────────┐
│  좌석 선택: VIP-A3                           │
│                                             │
│  [3D 뷰]  [실제 사진]  [AR 보기]            │
│                                             │
│  ┌───────────────────────────────────┐     │
│  │                                   │     │
│  │      [3D Venue Model]             │     │
│  │         (회전 가능)                │     │
│  │                                   │     │
│  │      현재 위치: VIP-A3             │     │
│  │      무대와의 거리: 15m            │     │
│  │      시야각: ⭐⭐⭐⭐⭐             │     │
│  │                                   │     │
│  └───────────────────────────────────┘     │
│                                             │
│  실제 이 좌석에서 본 뷰:                     │
│  ┌───────────────────────────────────┐     │
│  │   [User uploaded photo]           │     │
│  │   "정말 좋은 자리였어요!"          │     │
│  └───────────────────────────────────┘     │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 7. Smart Queue (AI 기반 대기열 최적화)

### 7.1 개요
머신러닝을 활용한 지능형 대기열 관리 시스템

### 7.2 ML 모델 활용
- **수요 예측**: LSTM 기반 티켓 판매 속도 예측
- **이상 탐지**: Isolation Forest로 봇 탐지
- **동적 할당**: 강화학습으로 서버 리소스 최적화

### 7.3 봇 탐지 알고리즘
```python
from sklearn.ensemble import IsolationForest

# 봇 탐지 feature
features = [
    'click_speed',           # 클릭 속도
    'mouse_movement',        # 마우스 움직임 패턴
    'keyboard_pattern',      # 키보드 입력 패턴
    'session_duration',      # 세션 시간
    'page_view_sequence',    # 페이지 방문 순서
    'device_fingerprint',    # 디바이스 지문
    'ip_reputation',         # IP 평판 점수
]

model = IsolationForest(contamination=0.1)
model.fit(historical_user_behavior)

# 실시간 탐지
is_bot = model.predict(current_user_features) == -1
if is_bot:
    block_user()
```

### 7.4 대기열 우선순위
```python
def calculate_queue_priority(user):
    priority_score = 0

    # Verified Fan 보너스
    if user.verified_fan_tier == 'Platinum':
        priority_score += 1000
    elif user.verified_fan_tier == 'Gold':
        priority_score += 500

    # 과거 구매 이력
    priority_score += user.past_purchases * 10

    # 접속 시간 (Early bird)
    early_seconds = (ticket_open_time - user.join_time).seconds
    priority_score += min(early_seconds, 300)  # 최대 5분

    # 봇 의심 페널티
    if user.bot_score > 0.7:
        priority_score -= 10000

    return priority_score
```

---

## 8. Multi-Event Pass (복합 이벤트 패키지)

### 8.1 개요
여러 공연을 묶어서 할인된 가격에 판매하는 시즌 패스 시스템

### 8.2 패키지 유형
- **시즌 패스**: 시리즈 전체 (예: 야구 시즌권)
- **페스티벌 패스**: 3일 페스티벌 전체 입장
- **아티스트 투어**: 동일 아티스트 여러 공연
- **장소 기반**: 특정 공연장 월간 패스

### 8.3 가격 책정
```python
def calculate_package_price(events, discount_rate=0.15):
    total_original = sum(event.base_price for event in events)
    package_price = total_original * (1 - discount_rate)

    # 추가 혜택
    perks = [
        "우선 좌석 선택",
        "무료 주차",
        "VIP 라운지 이용",
        "굿즈 10% 할인",
    ]

    return {
        'package_price': package_price,
        'savings': total_original - package_price,
        'perks': perks
    }
```

### 8.4 UI 표시
```
┌─────────────────────────────────────────────┐
│  🎵 BTS World Tour 시즌 패스                 │
├─────────────────────────────────────────────┤
│                                             │
│  포함된 공연:                                │
│  ✓ 서울 공연 (2024.05.20)                   │
│  ✓ 부산 공연 (2024.06.15)                   │
│  ✓ 대구 공연 (2024.07.01)                   │
│                                             │
│  개별 구매: ₩450,000                         │
│  패키지 가격: ₩382,500                       │
│  💰 절약: ₩67,500 (15% 할인)                │
│                                             │
│  추가 혜택:                                  │
│  ⭐ 우선 좌석 선택권                          │
│  ⭐ 무료 주차 3회                            │
│  ⭐ VIP 라운지 이용                          │
│  ⭐ 공식 굿즈 10% 할인                       │
│                                             │
│         [패키지로 구매하기]                  │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 9. Mobile Wallet Integration

### 9.1 지원 플랫폼
- **Apple Wallet** (PKPass)
- **Google Pay** (JWT)
- **Samsung Pay**

### 9.2 티켓 구성 요소
```json
{
  "formatVersion": 1,
  "passTypeIdentifier": "pass.com.ticketing.event",
  "serialNumber": "BK-2024052012345",
  "teamIdentifier": "YOUR_TEAM_ID",
  "organizationName": "Ticketing Pro",
  "description": "BTS World Tour 2024",
  "logoText": "Ticketing",
  "foregroundColor": "rgb(255, 255, 255)",
  "backgroundColor": "rgb(60, 65, 76)",
  "barcode": {
    "format": "PKBarcodeFormatQR",
    "message": "BK-2024052012345:rotating_token",
    "messageEncoding": "iso-8859-1"
  },
  "eventTicket": {
    "primaryFields": [
      {
        "key": "event",
        "label": "EVENT",
        "value": "BTS World Tour 2024"
      }
    ],
    "secondaryFields": [
      {
        "key": "loc",
        "label": "LOCATION",
        "value": "잠실 올림픽 주경기장"
      }
    ],
    "auxiliaryFields": [
      {
        "key": "date",
        "label": "DATE",
        "value": "2024.05.20 (토) 18:00"
      },
      {
        "key": "seat",
        "label": "SEAT",
        "value": "VIP-A3"
      }
    ]
  },
  "locations": [
    {
      "latitude": 37.5145,
      "longitude": 127.0731,
      "relevantText": "잠실 올림픽 주경기장에 도착했습니다!"
    }
  ]
}
```

---

## 10. Analytics & Insights (고급 분석)

### 10.1 실시간 대시보드 지표
- **판매 속도**: 초당 티켓 판매 수
- **전환율**: 페이지뷰 → 구매 전환
- **평균 대기 시간**: Queue에서 구매까지
- **이탈률**: 각 단계별 이탈률
- **수익 추세**: 실시간 매출 그래프

### 10.2 Funnel 분석
```
방문자 (100%)
    ↓ (-30%)
검색/탐색 (70%)
    ↓ (-20%)
이벤트 상세 (50%)
    ↓ (-15%)
좌석 선택 (35%)
    ↓ (-10%)
결제 정보 입력 (25%)
    ↓ (-5%)
결제 완료 (20%)
```

### 10.3 열 지도 (Heatmap)
- 좌석 선택 클릭 분포
- 페이지 스크롤 깊이
- 마우스 움직임 패턴
- 이탈 지점 시각화

### 10.4 사용자 세그먼트
```python
segments = {
    'VIP 고객': {
        'filter': lambda u: u.lifetime_value > 1000000,
        'count': 1234,
        'avg_purchase': 250000
    },
    '충성 고객': {
        'filter': lambda u: u.purchase_count > 5,
        'count': 5678,
        'avg_purchase': 150000
    },
    '신규 고객': {
        'filter': lambda u: u.purchase_count == 0,
        'count': 12345,
        'avg_purchase': 0
    },
    '이탈 위험': {
        'filter': lambda u: u.days_since_last_purchase > 180,
        'count': 3456,
        'avg_purchase': 80000
    }
}
```

---

## 11. API Rate Limiting 전략

### 11.1 계층별 제한
```yaml
rate_limits:
  anonymous:
    search: 10/min
    event_detail: 20/min
    booking: 0  # 로그인 필요

  authenticated:
    search: 50/min
    event_detail: 100/min
    booking: 20/min
    payment: 10/min

  verified_fan:
    search: 100/min
    event_detail: 200/min
    booking: 50/min
    payment: 30/min

  api_partner:
    search: 1000/min
    event_detail: 2000/min
    booking: 500/min
    payment: 200/min
```

### 11.2 Distributed Rate Limiting (Redis)
```python
import redis
import time

class DistributedRateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client

    def is_allowed(self, user_id, action, limit, window=60):
        key = f"ratelimit:{action}:{user_id}"
        current = int(time.time())
        window_start = current - window

        # Remove old entries
        self.redis.zremrangebyscore(key, 0, window_start)

        # Count requests in current window
        count = self.redis.zcard(key)

        if count < limit:
            # Add current request
            self.redis.zadd(key, {current: current})
            self.redis.expire(key, window)
            return True

        return False
```

---

## 12. Fraud Detection (부정 거래 탐지)

### 12.1 탐지 규칙
- **여러 계정에서 동일 카드 사용**
- **짧은 시간 내 대량 구매**
- **의심스러운 IP (VPN, Proxy)**
- **비정상적인 행동 패턴**
- **도용 카드 데이터베이스 대조**

### 12.2 머신러닝 모델
```python
from sklearn.ensemble import RandomForestClassifier

# Feature engineering
features = [
    'purchase_count_24h',
    'unique_events_purchased',
    'avg_time_between_purchases',
    'payment_method_diversity',
    'ip_reputation_score',
    'device_fingerprint_changes',
    'failed_payment_attempts',
    'account_age_days',
    'email_domain_reputation',
    'shipping_billing_mismatch',
]

# Train model
X_train, y_train = load_historical_fraud_data()
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Real-time prediction
fraud_probability = model.predict_proba(current_transaction)[0][1]

if fraud_probability > 0.8:
    action = "BLOCK"
elif fraud_probability > 0.5:
    action = "MANUAL_REVIEW"
else:
    action = "APPROVE"
```

### 12.3 2FA 강화 인증
```
┌─────────────────────────────────────────┐
│  ⚠️ 추가 인증이 필요합니다               │
├─────────────────────────────────────────┤
│                                         │
│  보안을 위해 본인 인증을 진행합니다       │
│                                         │
│  인증 방법 선택:                         │
│  ⚪ SMS 인증 (010-****-5678)            │
│  ⚪ 이메일 인증 (hong****@example.com)  │
│  ⚪ 생체 인증 (지문/얼굴)                │
│                                         │
│  [인증 코드 받기]                        │
│                                         │
└─────────────────────────────────────────┘
```

---

## 13. Accessibility (접근성) 고급 기능

### 13.1 장애인 좌석 예약
- **휠체어 좌석**: 전용 구역 표시
- **동반자 좌석**: 인접 좌석 자동 할당
- **시각 장애**: 스크린 리더 최적화
- **청각 장애**: 수화 통역 구역 표시

### 13.2 다국어 지원
```javascript
const languages = {
  'ko': '한국어',
  'en': 'English',
  'ja': '日本語',
  'zh-CN': '简体中文',
  'zh-TW': '繁體中文',
};

// 자동 번역 (Google Translate API)
async function translateContent(text, targetLang) {
  const response = await fetch('/api/translate', {
    method: 'POST',
    body: JSON.stringify({ text, targetLang })
  });
  return response.json();
}
```

---

## 14. Performance Optimization

### 14.1 CDN 전략
- **이미지**: Cloudflare Images
- **정적 파일**: S3 + CloudFront
- **API**: GraphQL Edge Caching
- **지역별 라우팅**: GeoDNS

### 14.2 Caching 전략
```yaml
cache_strategy:
  event_list:
    ttl: 300s  # 5분
    strategy: stale-while-revalidate

  event_detail:
    ttl: 60s  # 1분
    strategy: cache-first

  seat_availability:
    ttl: 0s  # 캐시 없음
    strategy: network-only

  user_profile:
    ttl: 3600s  # 1시간
    strategy: cache-first
```

### 14.3 Database Sharding
```python
# User ID 기반 샤딩
def get_shard(user_id):
    shard_count = 4
    shard_id = int(user_id, 16) % shard_count
    return f"db_shard_{shard_id}"

# Event ID 기반 샤딩
def get_event_shard(event_id):
    # 인기 이벤트는 전용 샤드
    if is_high_demand_event(event_id):
        return "db_shard_premium"
    else:
        return get_shard(event_id)
```

---

## 15. API 명세 (엔터프라이즈)

### 15.1 Queue Management API

```
POST /api/queue/join
Request:
{
  "event_id": "evt_123",
  "user_id": "usr_456",
  "verified_fan_tier": "gold"
}

Response:
{
  "queue_position": 1234,
  "estimated_wait_time": 480,  // seconds
  "queue_token": "jwt_token_here",
  "expires_at": "2024-05-20T10:15:00Z"
}
```

### 15.2 Dynamic Pricing API

```
GET /api/pricing/calculate
Query Params:
  - event_id: evt_123
  - section: VIP
  - quantity: 2

Response:
{
  "base_price": 150000,
  "current_price": 195000,
  "price_multiplier": 1.3,
  "factors": {
    "occupancy_rate": 0.85,
    "demand_score": 0.9,
    "time_to_event_days": 45
  },
  "price_history": [
    {"timestamp": "2024-03-01T00:00:00Z", "price": 150000},
    {"timestamp": "2024-03-15T00:00:00Z", "price": 180000},
    {"timestamp": "2024-04-01T00:00:00Z", "price": 195000}
  ]
}
```

### 15.3 SafeTix Generation API

```
POST /api/tickets/generate-safetix
Request:
{
  "booking_id": "BK-2024052012345"
}

Response:
{
  "ticket_id": "TIX-ABC123",
  "qr_code_data": "encrypted_rotating_data",
  "qr_code_image": "base64_image_data",
  "wallet_pass_url": "https://cdn.../ticket.pkpass",
  "expires_at": "2024-05-20T22:00:00Z",
  "rotation_interval": 60  // seconds
}
```

---

## 16. 구현 우선순위

### Phase 1: 핵심 기능 (즉시)
- ✅ 이미 구현됨: 기본 예약, 결제, API Gateway
- ⬜ Queue System (대기열)
- ⬜ SafeTix (동적 QR)
- ⬜ Rate Limiting 강화

### Phase 2: 차별화 기능 (1-2개월)
- ⬜ Verified Fan
- ⬜ Dynamic Pricing
- ⬜ 3D Seat View
- ⬜ Mobile Wallet

### Phase 3: 고급 기능 (3-6개월)
- ⬜ Official Platinum (리셀)
- ⬜ Multi-Event Pass
- ⬜ AI 봇 탐지
- ⬜ Fraud Detection ML

### Phase 4: 엔터프라이즈 (6개월+)
- ⬜ White-label Solution
- ⬜ API Marketplace
- ⬜ 블록체인 통합
- ⬜ Global CDN

---

**문서 버전**: 1.0
**최종 수정일**: 2024-01-16
**작성자**: Backend Team
**참고**: Ticketmaster, StubHub, SeatGeek 벤치마킹
