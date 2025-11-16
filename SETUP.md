# Ticketing Pro - 전체 시스템 설정 가이드

## 📋 개요

Ticketmaster Pro 수준의 엔터프라이즈 티켓팅 플랫폼 전체 시스템 설정 가이드입니다.

> **🎯 빠르게 시작하고 싶으신가요?** → [QUICKSTART.md](./QUICKSTART.md)로 이동!

## 🆕 개선 사항 (2024)

로컬 개발 환경이 대폭 개선되었습니다!

### ✨ 새로운 기능

1. **Docker Compose 통합** - 한 번의 명령으로 전체 시스템 시작
   ```bash
   make dev  # 끝!
   ```

2. **Makefile 자동화** - 50+ 개발 명령어 지원
   - `make up`, `make down`, `make logs`, `make restart` 등
   - 서비스별 제어: `make start service=auth`
   - 그룹 제어: `make start-infra`, `make start-services`

3. **Tilt 통합** - Kubernetes 로컬 개발 자동화
   - 코드 변경 시 자동 재빌드/배포
   - 실시간 로그 스트리밍
   - 통합 대시보드 (http://localhost:10350)

4. **통합 환경 변수** - 하나의 `.env` 파일로 모든 서비스 설정

### 🔧 개선된 워크플로우

**이전:**
```bash
# 각 서비스마다 수동 설정
cd services/auth && python -m venv venv && ...
cd services/events && python -m venv venv && ...
# PostgreSQL 설치, Redis 설치, ...
# 8개 터미널에서 각각 실행
```

**지금:**
```bash
make dev  # 모든 것이 자동으로 시작됨
```

## 📚 목차

- [빠른 시작](#-빠른-시작) - 3가지 방법으로 시작하기
- [Docker Compose 가이드](#-docker-compose-상세-가이드) - 로컬 개발 (권장)
- [Tilt + Kubernetes 가이드](#️-tilt--kubernetes-상세-가이드) - 프로덕션 환경
- [환경 변수 설정](#-환경-변수-설정) - 상세 설정
- [데이터베이스 설정](#️-데이터베이스-설정) - DB 초기화
- [트러블슈팅](#-트러블슈팅) - 문제 해결
- [보안 체크리스트](#-보안-체크리스트) - 배포 전 확인

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│                    React + TypeScript                       │
│              (Virtual Waiting Room, SafeTix)                │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                            │
│              FastAPI + Rate Limiting                        │
└─────┬───────────┬────────────┬───────────┬─────────────┬────┘
      │           │            │           │             │
      ↓           ↓            ↓           ↓             ↓
┌─────────┐  ┌────────┐   ┌────────┐   ┌────────┐   ┌─────────┐
│  Auth   │  │Events  │   │Booking │   │Payment │   │ Search  │
│Service  │  │Service │   │Service │   │Service │   │ Service │
└─────────┘  └────────┘   └────────┘   └────────┘   └─────────┘
                              │
                              ↓
                        ┌────────────┐
                        │ Inventory  │
                        │ (Go/gRPC)  │
                        └────────────┘
```

---

## 🚀 빠른 시작

> **💡 권장:** [QUICKSTART.md](./QUICKSTART.md)에서 3가지 간편한 시작 방법을 확인하세요!

### 방법 1: Docker Compose (가장 간단 ⭐)

```bash
# 1단계: 초기 설정
make init

# 2단계: 전체 시스템 시작 + DB 초기화
make dev

# 접속
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### 방법 2: Tilt + Kubernetes (프로덕션 환경)

```bash
# 사전 준비
brew install minikube tilt
minikube start --cpus=4 --memory=8192
eval $(minikube docker-env)

# Tilt 실행 (자동 빌드/배포)
tilt up
```

### 방법 3: 수동 실행 (개별 서비스 제어)

<details>
<summary>클릭하여 상세 가이드 보기</summary>

#### 1. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

#### 2. API Gateway 실행

```bash
cd services/api-gateway
python -m venv venv
source venv/bin/activate
uv pip install --system -r pyproject.toml
uvicorn app.main:app --reload --port 8000
```

#### 3. 백엔드 서비스 실행

각 서비스별로 동일한 패턴:

```bash
cd services/{service-name}
python -m venv venv
source venv/bin/activate
uv pip install --system -r pyproject.toml
uvicorn app.main:app --reload --port {PORT}
```

**포트 할당:**
- Auth: 8001 | Events: 8002 | Booking: 8003
- Payment: 8004 | Search: 8005 | Notification: 8006
- Inventory: 50051 (gRPC)

#### 4. Inventory Service (Go)

```bash
cd services/inventory

# Protobuf 컴파일 (최초 1회)
protoc --go_out=. --go-grpc_out=. proto/inventory.proto

# 의존성 설치 및 실행
go mod download
go run cmd/server/main.go
```

</details>

---

## 🔧 환경 변수 설정

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000/api
VITE_STRIPE_PUBLIC_KEY=pk_test_your_key
```

### API Gateway (.env)

```env
CORS_ORIGINS=http://localhost:3000

AUTH_SERVICE_URL=http://localhost:8001
EVENTS_SERVICE_URL=http://localhost:8002
BOOKING_SERVICE_URL=http://localhost:8003
PAYMENT_SERVICE_URL=http://localhost:8004
SEARCH_SERVICE_URL=http://localhost:8005

DD_SERVICE=api-gateway
DD_ENV=development
```

### Auth Service (.env)

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/ticketing
JWT_SECRET_KEY=your-super-secret-key-change-this
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15

DD_SERVICE=auth-service
DD_ENV=development
```

### Events Service (.env)

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/ticketing
AWS_REGION=us-east-1

DD_SERVICE=events-service
DD_ENV=development
```

### Booking Service (.env)

```env
DYNAMODB_TABLE_NAME=bookings
AWS_REGION=us-east-1

KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_PRODUCER_TOPIC=booking-events

INVENTORY_GRPC_HOST=localhost
INVENTORY_GRPC_PORT=50051

DD_SERVICE=booking-service
DD_ENV=development
```

### Payment Service (.env)

```env
STRIPE_SECRET_KEY=sk_test_your_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

BOOKING_SERVICE_URL=http://localhost:8003

DD_SERVICE=payment-service
DD_ENV=development
```

### Search Service (.env)

```env
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
OPENSEARCH_USE_SSL=false

AWS_REGION=us-east-1

DD_SERVICE=search-service
DD_ENV=development
```

### Notification Service (.env)

```env
AWS_REGION=us-east-1
SES_FROM_EMAIL=noreply@ticketing.com

KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_CONSUMER_GROUP=notification-service

DD_SERVICE=notification-service
DD_ENV=development
```

---

## 🗄️ 데이터베이스 설정

### PostgreSQL (Auth, Events)

```bash
# PostgreSQL 설치 및 실행
brew install postgresql@14  # macOS
sudo apt-get install postgresql-14  # Ubuntu

# 데이터베이스 생성
createdb ticketing

# 마이그레이션 (각 서비스에서)
alembic upgrade head
```

### DynamoDB Local (Booking)

```bash
# Docker로 실행
docker run -p 8000:8000 amazon/dynamodb-local

# 테이블 생성
aws dynamodb create-table \
  --table-name bookings \
  --attribute-definitions \
      AttributeName=booking_id,AttributeType=S \
  --key-schema \
      AttributeName=booking_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --endpoint-url http://localhost:8000
```

### Redis (Cache, Queue)

```bash
# Redis 설치 및 실행
brew install redis  # macOS
sudo apt-get install redis-server  # Ubuntu

# 실행
redis-server
```

### OpenSearch (Search)

```bash
# Docker로 실행
docker run -p 9200:9200 -p 9600:9600 \
  -e "discovery.type=single-node" \
  opensearchproject/opensearch:latest
```

### Kafka (Event Streaming)

```bash
# Docker Compose로 실행
docker-compose up -d kafka zookeeper
```

---

## 🎯 주요 기능 테스트

### 1. 회원가입 및 로그인

1. `http://localhost:3000/register`에서 회원가입
2. `http://localhost:3000/login`에서 로그인

### 2. 이벤트 검색

1. 메인 페이지에서 검색어 입력
2. 카테고리 필터링 테스트

### 3. 좌석 선택 및 예약

1. 이벤트 클릭
2. "좌석선택" 탭으로 이동
3. 좌석 클릭 (최대 4석)
4. "예매하기" 버튼 클릭

### 4. Virtual Waiting Room (대기열)

- 인기 이벤트에서 자동으로 대기열 페이지로 이동
- 실시간 순번 업데이트 확인

### 5. 결제 (Stripe)

1. 결제 페이지에서 카드 정보 입력
2. 테스트 카드: `4242 4242 4242 4242`
3. 만료일: 미래 날짜 (예: 12/25)
4. CVC: 아무 3자리 (예: 123)

### 6. SafeTix (동적 QR)

1. 결제 완료 후 "티켓 보기"
2. QR 코드가 60초마다 자동 갱신되는지 확인

---

## 🐛 트러블슈팅

### CORS 에러

API Gateway의 CORS 설정 확인:
```python
# services/api-gateway/app/main.py
allow_origins=["http://localhost:3000"]
```

### Stripe 결제 실패

1. Stripe 공개 키 확인
2. Webhook Secret 설정 확인
3. Stripe CLI로 Webhook 테스트:
```bash
stripe listen --forward-to localhost:8004/payments/webhook
```

### Database Connection 에러

1. PostgreSQL 실행 상태 확인
2. `.env`의 `DATABASE_URL` 확인
3. 데이터베이스 존재 여부 확인

---

## 📦 Docker Compose 상세 가이드

### 기본 명령어

```bash
# 🚀 빠른 시작 (추천)
make dev                      # 초기화 + 시작 + DB 설정

# 또는 단계별
make init                     # 환경 변수 파일 생성
make up                       # 전체 시스템 시작
make init-db                  # DynamoDB 테이블 생성
```

### 서비스 제어

```bash
# 상태 확인
make ps                       # 실행 중인 서비스 확인

# 전체 제어
make down                     # 전체 중지
make restart                  # 전체 재시작
make build                    # 이미지 재빌드
make rebuild                  # 캐시 없이 재빌드

# 그룹별 제어
make start-infra             # 인프라만 시작
make stop-infra              # 인프라만 중지
make start-services          # 앱 서비스만 시작
make stop-services           # 앱 서비스만 중지

# 개별 서비스
make start service=auth      # Auth 서비스 시작
make stop service=auth       # Auth 서비스 중지
make restart service=auth    # Auth 서비스 재시작
make logs service=auth       # Auth 로그 확인
```

### 로그 및 디버깅

```bash
# 로그 확인
make logs                     # 전체 로그 (실시간)
make logs service=auth        # 특정 서비스 로그

# 컨테이너 접속
make shell service=auth       # 쉘 접속
make exec service=auth cmd='pytest'  # 명령어 실행
```

### 데이터베이스 관리

```bash
# DynamoDB 테이블 초기화
make init-db

# PostgreSQL 마이그레이션
make migrate

# 초기 데이터 삽입 (TODO)
make seed
```

### 정리

```bash
# 일반 정리
make down                     # 컨테이너만 중지

# 완전 정리 (데이터 삭제)
make clean                    # 볼륨 포함 전체 삭제

# Docker 시스템 정리
make prune                    # 미사용 리소스 삭제
```

### 환경 변수

루트 디렉토리의 `.env` 파일 하나로 모든 서비스 설정:

```bash
# .env.example 복사
cp .env.example .env

# 필수 수정 항목
vim .env
# - STRIPE_SECRET_KEY
# - STRIPE_WEBHOOK_SECRET
# - JWT_SECRET_KEY
```

---

## ☸️ Tilt + Kubernetes 상세 가이드

### Tilt 사용 (권장)

**Tilt**는 Kubernetes 로컬 개발을 자동화하는 도구입니다. 코드 변경 시 자동으로 재빌드/배포됩니다.

```bash
# 1. Minikube & Tilt 설치
brew install minikube kubectl tilt

# 2. Minikube 시작
minikube start --cpus=4 --memory=8192
eval $(minikube docker-env)

# 3. Tilt 실행
tilt up

# Tilt UI 자동 열림: http://localhost:10350
```

**Tilt UI에서 할 수 있는 것:**
- 📊 모든 서비스 상태 한눈에 확인
- 📜 실시간 로그 스트리밍 (서비스별 탭)
- 🔄 빌드/배포 진행 상황 모니터링
- ⚡ 코드 변경 감지 → 자동 재빌드/배포
- 🔧 서비스별 재시작/재빌드 버튼

**종료:**
```bash
tilt down                     # Tilt 종료
minikube stop                 # Minikube 중지
```

### 수동 배포 (Tilt 없이)

<details>
<summary>수동으로 kubectl 사용하기 (클릭하여 펼치기)</summary>

```bash
# 1. Minikube 시작
minikube start --cpus=4 --memory=8192
eval $(minikube docker-env)

# 2. 네임스페이스 및 설정 생성
kubectl apply -f k8s/local/namespace.yaml
kubectl apply -f k8s/local/configmap.yaml
kubectl apply -f k8s/local/secrets.yaml

# 3. 이미지 빌드
for service in api-gateway auth events booking payment search notification inventory; do
  docker build -t ticketing/${service}-service:local ./services/$service
done
docker build -t ticketing/frontend:local ./frontend

# 4. 인프라 배포
kubectl apply -f k8s/local/postgres.yaml
kubectl apply -f k8s/local/redis.yaml
kubectl apply -f k8s/local/dynamodb.yaml
kubectl apply -f k8s/local/opensearch.yaml
kubectl apply -f k8s/local/kafka.yaml

# 5. 애플리케이션 배포
kubectl apply -f k8s/local/

# 6. 상태 확인
kubectl get pods -n ticketing-local
kubectl get svc -n ticketing-local

# 7. 서비스 접근 (포트 포워딩)
kubectl port-forward -n ticketing-local svc/api-gateway 8000:8000
kubectl port-forward -n ticketing-local svc/frontend 3000:80

# 8. 로그 확인
kubectl logs -f -n ticketing-local deployment/auth-service

# 9. 재배포 (코드 수정 후)
docker build -t ticketing/auth-service:local ./services/auth
kubectl rollout restart -n ticketing-local deployment/auth-service

# 10. 정리
kubectl delete namespace ticketing-local
minikube stop
```

</details>

### Kubernetes 개발 팁

```bash
# 특정 서비스 로그만 보기 (Tilt UI 대신)
kubectl logs -f -n ticketing-local deployment/auth-service

# Pod 상태 확인
kubectl get pods -n ticketing-local -w

# Pod 내부 접속
kubectl exec -it -n ticketing-local deployment/auth-service -- /bin/sh

# 서비스 재시작
kubectl rollout restart -n ticketing-local deployment/auth-service

# DynamoDB 테이블 생성
kubectl port-forward -n ticketing-local svc/dynamodb-local 8001:8000
./scripts/init-dynamodb.sh
```

---

## 🔐 보안 체크리스트

- [ ] JWT Secret 변경
- [ ] Stripe Secret Key 설정
- [ ] PostgreSQL 비밀번호 변경
- [ ] CORS origins 프로덕션 URL로 변경
- [ ] Rate limiting 설정 확인
- [ ] HTTPS 활성화 (프로덕션)

---

## 📊 모니터링

### Datadog APM (선택 사항)

각 서비스의 `.env`에 설정:
```env
DD_AGENT_HOST=localhost
DD_TRACE_ENABLED=true
DD_SERVICE=service-name
DD_ENV=development
```

### Prometheus Metrics

각 서비스는 `/metrics` 엔드포인트 제공:
- http://localhost:8001/metrics (Auth)
- http://localhost:8002/metrics (Events)
- ...

---

## 🚢 프로덕션 배포

### 1. 환경 변수 설정

모든 `.env` 파일의 값을 프로덕션 환경에 맞게 변경

### 2. 프론트엔드 빌드

```bash
cd frontend
npm run build
# dist 폴더를 CDN 또는 S3에 배포
```

### 3. 백엔드 배포

- Docker 이미지 빌드
- ECR에 푸시
- EKS에 배포 (Kubernetes manifests 사용)

### 4. 데이터베이스 마이그레이션

```bash
# 각 서비스에서
alembic upgrade head
```

---

## 📝 다음 단계

1. **테스트 작성**: Unit, Integration, E2E 테스트
2. **CI/CD 파이프라인**: GitHub Actions 설정
3. **성능 최적화**: Caching, CDN 설정
4. **고급 기능**: Dynamic Pricing, Verified Fan 완성

---

## 💬 지원

문제가 발생하면 다음을 확인하세요:

1. 모든 서비스가 실행 중인지
2. 환경 변수가 올바르게 설정되었는지
3. 데이터베이스 연결이 정상인지
4. 로그를 확인

---
