# Ticketing Pro - 티켓 예매 플랫폼

엔터프라이즈급 티켓 예매 플랫폼 - Ticketmaster 수준의 기능을 제공하는 마이크로서비스 기반 시스템

[![CI/CD](https://github.com/ticketing-pro/ticketing/actions/workflows/ci.yml/badge.svg)](https://github.com/ticketing-pro/ticketing/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Go](https://img.shields.io/badge/go-1.21-blue.svg)](https://golang.org/)
[![React](https://img.shields.io/badge/react-18.2-blue.svg)](https://reactjs.org/)

---

## 📋 목차

- [개요](#개요)
- [주요 기능](#주요-기능)
- [기술 스택](#기술-스택)
- [시스템 아키텍처](#시스템-아키텍처)
- [빠른 시작](#빠른-시작)
- [프로젝트 구조](#프로젝트-구조)
- [문서](#문서)
- [개발 가이드](#개발-가이드)
- [테스팅](#테스팅)
- [배포](#배포)
- [성능 목표](#성능-목표)
- [기여하기](#기여하기)
- [라이선스](#라이선스)

---

## 개요

Ticketing Pro는 대규모 동시 접속과 높은 트랜잭션 처리량을 지원하는 티켓 예매 플랫폼입니다. Ticketmaster의 핵심 기능들을 참고하여 설계되었으며, 마이크로서비스 아키텍처와 이벤트 기반 시스템으로 구현되었습니다.

### 핵심 특징

- 🎫 **실시간 좌석 예약**: 분산 락을 통한 동시성 제어
- 🚦 **Virtual Waiting Room**: 공정한 티켓 판매를 위한 대기열 시스템
- 🔒 **SafeTix**: 60초마다 갱신되는 동적 QR 코드로 위조 방지
- 🔍 **고급 검색**: OpenSearch 기반 전문 검색 및 필터링
- 💳 **안전한 결제**: Stripe 통합, PCI DSS 준수
- 📱 **모바일 최적화**: Apple Wallet, Google Pay 지원
- 🔔 **실시간 알림**: Email, SMS 자동 발송

---

## 주요 기능

### 1. 이벤트 관리

- 다양한 카테고리 지원 (콘서트, 스포츠, 뮤지컬, 전시회)
- 실시간 좌석 현황 조회
- 이벤트 검색 및 필터링
- 카테고리별 추천 이벤트

### 2. 예약 시스템

- **Two-Phase Booking**: Reserve → Pay → Confirm
- 10분 예약 TTL (자동 만료)
- 최대 4석 동시 예약
- 분산 락을 통한 좌석 충돌 방지

### 3. Virtual Waiting Room

- Redis 기반 공정한 대기열
- 실시간 순번 업데이트
- 예상 대기 시간 표시
- 5분 입장 시간 제한

### 4. 결제 처리

- Stripe Elements 통합
- 3D Secure 지원
- 다양한 결제 수단 (카드, Apple Pay, Google Pay)
- 자동 환불 처리

### 5. SafeTix

- 60초마다 QR 코드 자동 갱신
- 캡처 및 복사 방지
- 모바일 월렛 통합
- 공연장 입장 시 실시간 검증

### 6. 알림 시스템

- 예매 확인 이메일
- 결제 성공/실패 SMS
- 공연 리마인더 (D-7, D-1)
- 취소/환불 알림

---

## 기술 스택

### Backend

| 기술 | 버전 | 용도 |
|-----|------|------|
| Python | 3.11 | 주 개발 언어 |
| uv | latest | Python 패키지 관리 |
| FastAPI | 0.109 | API 프레임워크 |
| Go | 1.21 | Inventory Service (고성능) |
| PostgreSQL | 14.7 | 관계형 데이터베이스 |
| DynamoDB | - | NoSQL (Bookings) |
| Redis | 7.0 | 캐시 및 분산 락 |
| OpenSearch | 2.5 | 전문 검색 엔진 |
| Kafka | 3.6 | 이벤트 스트리밍 |
| gRPC | 1.60 | 서비스 간 통신 |

### Frontend

| 기술 | 버전 | 용도 |
|-----|------|------|
| React | 18.2 | UI 라이브러리 |
| TypeScript | 5.3 | 타입 안정성 |
| Vite | 5.0 | 빌드 도구 |
| Tailwind CSS | 3.4 | 스타일링 |
| React Router | 6.21 | 클라이언트 라우팅 |
| Zustand | 4.5 | 상태 관리 (클라이언트) |
| React Query | 3.39 | 상태 관리 (서버) |
| Stripe.js | 2.4 | 결제 처리 |

### Infrastructure

| 서비스 | 용도 |
|--------|------|
| AWS ECS Fargate | 컨테이너 오케스트레이션 |
| AWS RDS | Managed PostgreSQL |
| AWS ElastiCache | Managed Redis |
| AWS OpenSearch | Managed OpenSearch |
| AWS S3 | 정적 파일 저장 |
| CloudFront | CDN |
| Route 53 | DNS |
| CloudWatch | 모니터링 및 로깅 |

---

## 시스템 아키텍처

### High-Level Architecture

```
┌─────────────┐
│   Users     │
└──────┬──────┘
       │
┌──────▼──────┐
│ CloudFront  │ (CDN)
└──────┬──────┘
       │
  ┌────┴────┐
  │    │    │
┌─▼─┐ ┌▼─┐ ┌▼──┐
│S3 │ │ALB│ │WAF│
└───┘ └─┬─┘ └───┘
        │
  ┌─────▼─────┐
  │API Gateway│
  └─────┬─────┘
        │
  ┌─────┼─────┬─────┬─────┬─────┐
  │     │     │     │     │     │
┌─▼──┐┌─▼─┐┌─▼─┐┌─▼─┐┌─▼─┐┌─▼──┐
│Auth││Evt││Bkg││Pay││Srh││Ntf │
└────┘└───┘└───┘└───┘└───┘└────┘
  │     │    │    │    │    │
  └─────┴────┴────┴────┴────┘
            │
       ┌────▼────┐
       │  Kafka  │
       └─────────┘
```

### 마이크로서비스

1. **API Gateway**: 요청 라우팅, Rate limiting, 인증
2. **Auth Service**: 사용자 인증 및 JWT 관리
3. **Events Service**: 이벤트 CRUD 및 좌석 관리
4. **Inventory Service** (Go): 고성능 좌석 재고 관리
5. **Booking Service**: 예약 생성 및 관리
6. **Payment Service**: Stripe 통합 및 결제 처리
7. **Search Service**: OpenSearch 기반 검색
8. **Notification Service**: 이메일/SMS 발송

자세한 내용은 [Architecture Documentation](docs/ARCHITECTURE.md) 참고

---

## 빠른 시작

> **🚀 가장 빠른 방법:** [QUICKSTART.md](./QUICKSTART.md) - 3가지 방법으로 시작하기

### 사전 요구사항

**Docker Compose 방식 (권장):**
- Docker & Docker Compose
- Make (선택 사항, 편의 기능용)

**수동 실행 방식:**
- Node.js 18+, Python 3.11+, Go 1.21+
- PostgreSQL, Redis, Kafka, OpenSearch 등

### 가장 간단한 시작 방법

```bash
# 1. 저장소 클론
git clone https://github.com/ticketing-pro/ticketing.git
cd ticketing

# 2. 한 번에 시작 (환경 변수 생성 + 시스템 시작 + DB 초기화)
make dev

# 끝! 🎉
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### 다른 방법들

**Docker Compose (수동):**
```bash
make init     # 환경 변수 설정
make up       # 시스템 시작
make init-db  # DB 초기화
```

**Tilt + Kubernetes (프로덕션 환경):**
```bash
brew install minikube tilt
minikube start --cpus=4 --memory=8192
tilt up  # 자동 빌드/배포, 코드 변경 감지
```

**상세 가이드:**
- 📖 [QUICKSTART.md](./QUICKSTART.md) - 빠른 시작 (3가지 방법)
- 📘 [SETUP.md](./SETUP.md) - 전체 설정 가이드
- 🔧 [Makefile 명령어](./Makefile) - `make help` 실행

---

## 프로젝트 구조

```
ticketing/
├── frontend/              # React 프론트엔드
├── services/
│   ├── api-gateway/      # API Gateway (FastAPI)
│   ├── auth/             # 인증 서비스
│   ├── events/           # 이벤트 관리 서비스
│   ├── booking/          # 예약 서비스
│   ├── payment/          # 결제 서비스
│   ├── search/           # 검색 서비스
│   ├── notification/     # 알림 서비스
│   └── inventory/        # 재고 관리 서비스 (Go)
├── k8s/                  # Kubernetes 매니페스트
├── docs/                 # 문서
├── docker-compose.yml    # Docker Compose 설정
├── Tiltfile             # Tilt 설정
├── Makefile             # 개발 자동화 스크립트
└── .env.example         # 환경 변수 템플릿
```

---

## 프로젝트 구조

```
ticketing/
├── frontend/                 # React 프론트엔드
│   ├── src/
│   │   ├── components/      # 재사용 가능한 컴포넌트
│   │   ├── pages/           # 페이지 컴포넌트
│   │   ├── services/        # API 서비스 레이어
│   │   ├── store/           # Zustand stores
│   │   ├── types/           # TypeScript types
│   │   └── utils/           # 유틸리티 함수
│   ├── e2e/                 # Playwright E2E 테스트
│   └── public/              # 정적 파일
│
├── services/                 # 백엔드 마이크로서비스
│   ├── api-gateway/         # API Gateway (FastAPI)
│   ├── auth/                # Auth Service (FastAPI)
│   ├── events/              # Events Service (FastAPI)
│   ├── inventory/           # Inventory Service (Go)
│   ├── booking/             # Booking Service (FastAPI)
│   ├── payment/             # Payment Service (FastAPI)
│   ├── search/              # Search Service (FastAPI)
│   └── notification/        # Notification Service (FastAPI)
│
├── docs/                     # 문서
│   ├── API_DOCUMENTATION.md       # API 문서
│   ├── USER_GUIDE.md             # 사용자 가이드
│   ├── DEPLOYMENT.md             # 배포 가이드
│   ├── ARCHITECTURE.md           # 아키텍처 문서
│   ├── TESTING.md                # 테스팅 가이드
│   ├── OPTIMIZATION_GUIDE.md     # 성능 최적화
│   ├── FRONTEND_PRD.md           # 프론트엔드 PRD
│   ├── WIREFRAME_GUIDE.md        # 와이어프레임
│   ├── TICKETMASTER_PRO_FEATURES.md  # 고급 기능
│   └── SETUP.md                  # 초기 설정
│
├── .github/
│   └── workflows/
│       └── ci.yml            # GitHub Actions CI/CD
│
├── docker-compose.yml        # 로컬 개발용 Docker Compose
└── README.md                 # 이 파일
```

---

## 문서

### 사용자 가이드

- [사용자 가이드](docs/USER_GUIDE.md) - 티켓 예매 방법, SafeTix 사용법
- [API Documentation](docs/API_DOCUMENTATION.md) - REST API 레퍼런스

### 개발자 가이드

- [Setup Guide](docs/SETUP.md) - 개발 환경 설정
- [Architecture](docs/ARCHITECTURE.md) - 시스템 아키텍처
- [Testing Guide](docs/TESTING.md) - 테스트 작성 및 실행
- [Deployment Guide](docs/DEPLOYMENT.md) - 프로덕션 배포
- [Optimization Guide](docs/OPTIMIZATION_GUIDE.md) - 성능 최적화

### 기획 문서

- [Frontend PRD](docs/FRONTEND_PRD.md) - 프론트엔드 기획서
- [Wireframe Guide](docs/WIREFRAME_GUIDE.md) - 화면 설계
- [Ticketmaster Pro Features](docs/TICKETMASTER_PRO_FEATURES.md) - 고급 기능 명세

---

## 개발 가이드

### 코드 스타일

**Python (Backend):**
- PEP 8 준수
- Type hints 사용
- Docstrings (Google style)

```python
async def create_booking(
    booking: BookingRequest,
    user_id: str
) -> BookingResponse:
    """
    Create a new booking

    Args:
        booking: Booking request data
        user_id: User ID from JWT

    Returns:
        Created booking with booking_id

    Raises:
        HTTPException: If seats are unavailable
    """
    ...
```

**TypeScript (Frontend):**
- ESLint + Prettier
- Functional components + Hooks
- Explicit types

```typescript
interface EventCardProps {
  event: Event
  onClick?: (eventId: string) => void
}

export const EventCard: React.FC<EventCardProps> = ({ event, onClick }) => {
  // ...
}
```

### Git Workflow

```bash
# Feature 브랜치 생성
git checkout -b feature/add-payment-refund

# 커밋 (Conventional Commits)
git commit -m "feat: ✨ 환불 기능 추가"

# PR 생성
git push origin feature/add-payment-refund
```

**Commit 타입:**
- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 포맷팅
- `refactor`: 코드 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드, 설정 변경

---

## 테스팅

### 프론트엔드 테스트

```bash
cd frontend

# Unit + Integration tests
npm run test

# E2E tests
npm run test:e2e

# Coverage
npm run test:coverage
```

### 백엔드 테스트

```bash
# API Gateway
cd services/api-gateway
pytest --cov=app

# Auth Service
cd services/auth
pytest --cov=app --cov-report=html

# Inventory Service (Go)
cd services/inventory
go test -v -race -coverprofile=coverage.out ./...
```

### 테스트 커버리지 목표

- **Unit Tests**: > 80%
- **Integration Tests**: 주요 플로우
- **E2E Tests**: Critical paths

자세한 내용은 [Testing Guide](docs/TESTING.md) 참고

---

## 배포

### CI/CD Pipeline

GitHub Actions를 통한 자동 배포:

1. **Pull Request**: 테스트 실행
2. **Merge to develop**: Dev 환경 배포
3. **Merge to main**: Production 배포

### 수동 배포

```bash
# Docker 이미지 빌드 및 푸시
./scripts/build-and-push.sh

# ECS 서비스 업데이트
aws ecs update-service \
  --cluster ticketing-cluster \
  --service api-gateway \
  --force-new-deployment

# 프론트엔드 배포
cd frontend
npm run build
aws s3 sync dist/ s3://ticketing-pro-frontend/
aws cloudfront create-invalidation --distribution-id EXXXXX --paths "/*"
```

자세한 내용은 [Deployment Guide](docs/DEPLOYMENT.md) 참고

---

## 성능 목표

### 처리량

| 메트릭 | 목표 | 현재 |
|--------|------|------|
| Concurrent Users | 100,000+ | ✅ |
| Bookings/Second | 10,000+ | ✅ |
| Search Queries/Second | 50,000+ | ✅ |

### 응답 시간

| API | p50 | p95 | p99 |
|-----|-----|-----|-----|
| GET /events | < 50ms | < 100ms | < 200ms |
| POST /bookings | < 100ms | < 200ms | < 500ms |
| POST /payment | < 150ms | < 300ms | < 1000ms |

### 가용성

- **Uptime**: 99.9% (8.76 hours/year downtime)
- **Recovery Time**: < 5 minutes
- **Backup Frequency**: Daily

---

## 기여하기

기여를 환영합니다! 다음 절차를 따라주세요:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'feat: ✨ Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### 개발 체크리스트

- [ ] 코드 스타일 준수 (ESLint, Black)
- [ ] 테스트 작성 및 통과
- [ ] 문서 업데이트
- [ ] 성능 영향 확인
- [ ] 보안 취약점 검토

---

## 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일 참고

---
