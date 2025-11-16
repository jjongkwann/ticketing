# Ticketing Pro - 전체 시스템 설정 가이드

## 📋 개요

Ticketmaster Pro 수준의 엔터프라이즈 티켓팅 플랫폼 전체 시스템 설정 가이드입니다.

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

### 1. 프론트엔드 실행

```bash
cd frontend

# 환경 변수 설정
cp .env.example .env
# .env 파일을 열어서 값을 설정하세요

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

프론트엔드는 `http://localhost:3000`에서 실행됩니다.

### 2. API Gateway 실행

```bash
cd services/api-gateway

# uv 설치 (아직 설치하지 않은 경우)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 가상환경 생성 (선택 사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치 (uv 사용)
uv pip install --system -r pyproject.toml

# 환경 변수 설정
cp .env.example .env

# 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 백엔드 서비스 실행

각 서비스별로 동일한 패턴 (Python 서비스):

```bash
cd services/{service-name}

# 가상환경 생성 (선택 사항)
python -m venv venv
source venv/bin/activate

# 의존성 설치 (uv 사용)
uv pip install --system -r pyproject.toml

# 환경 변수 설정
cp .env.example .env

# 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port {PORT} --reload
```

**포트 할당:**
- Auth Service: 8001
- Events Service: 8002
- Booking Service: 8003
- Payment Service: 8004
- Search Service: 8005
- Notification Service: 8006
- Inventory Service: 50051 (gRPC)

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

## 📦 Docker로 전체 시스템 실행

```bash
# 전체 시스템 빌드 및 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down
```

---

## ☸️ Kubernetes로 로컬 실행 (권장)

로컬에서 프로덕션과 유사한 환경으로 실행하려면 Kubernetes를 사용하세요.

### 사전 요구사항

```bash
# Minikube 설치
brew install minikube kubectl

# Minikube 시작 (CPU 4코어, 메모리 8GB)
minikube start --cpus=4 --memory=8192

# Docker 환경 연결 (로컬 이미지 사용)
eval $(minikube docker-env)
```

### 이미지 빌드

```bash
# 모든 서비스 이미지 한번에 빌드
for service in api-gateway auth events booking payment search notification; do
  cd services/$service
  docker build -t ticketing/${service}-service:local .
  cd ../..
done
```

### 인프라 서비스 실행

```bash
# 네임스페이스 생성
kubectl create namespace ticketing-local

# PostgreSQL
kubectl run postgres --image=postgres:14 \
  --env="POSTGRES_PASSWORD=postgres" \
  --env="POSTGRES_DB=ticketing" \
  --port=5432 -n ticketing-local
kubectl expose pod postgres --port=5432 -n ticketing-local

# Redis
kubectl run redis --image=redis:7-alpine --port=6379 -n ticketing-local
kubectl expose pod redis --port=6379 -n ticketing-local

# Kafka
kubectl run kafka --image=apache/kafka:latest \
  --env="KAFKA_NODE_ID=1" \
  --env="KAFKA_PROCESS_ROLES=broker,controller" \
  --env="KAFKA_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093" \
  --env="KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092" \
  --env="KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER" \
  --env="KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT" \
  --env="KAFKA_CONTROLLER_QUORUM_VOTERS=1@kafka:9093" \
  --port=9092 -n ticketing-local
kubectl expose pod kafka --port=9092 -n ticketing-local

# OpenSearch
kubectl run opensearch --image=opensearchproject/opensearch:latest \
  --env="discovery.type=single-node" \
  --env="DISABLE_SECURITY_PLUGIN=true" \
  --port=9200 -n ticketing-local
kubectl expose pod opensearch --port=9200 -n ticketing-local
```

### 애플리케이션 배포

```bash
# ConfigMap과 Secret 생성
kubectl apply -f k8s/local/configmap.yaml
kubectl apply -f k8s/local/secrets.yaml

# 모든 서비스 배포
kubectl apply -f k8s/local/

# 상태 확인
kubectl get pods -n ticketing-local
kubectl get svc -n ticketing-local
```

### 서비스 접근

```bash
# API Gateway 접근 (자동으로 브라우저 열림)
minikube service api-gateway -n ticketing-local

# 또는 포트 포워딩으로 접근
kubectl port-forward svc/api-gateway 8000:8000 -n ticketing-local
# http://localhost:8000 접속
```

### 개발 워크플로우

```bash
# 코드 수정 후 재배포
cd services/api-gateway
docker build -t ticketing/api-gateway-service:local .
kubectl rollout restart deployment/api-gateway -n ticketing-local

# 로그 확인
kubectl logs -f deployment/api-gateway -n ticketing-local

# Pod 내부 접속 (디버깅)
kubectl exec -it deployment/api-gateway -n ticketing-local -- /bin/sh
```

### 정리

```bash
# 모든 리소스 삭제
kubectl delete namespace ticketing-local

# Minikube 중지
minikube stop

# Minikube 완전 삭제
minikube delete
```

**자세한 가이드**: [k8s/local/README.md](k8s/local/README.md)

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
