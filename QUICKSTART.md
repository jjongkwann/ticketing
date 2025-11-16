# 🚀 Ticketing Pro - 빠른 시작 가이드

로컬 개발 환경을 **3가지 방법**으로 시작할 수 있습니다.

---

## 방법 1: Docker Compose (권장 - 가장 간단)

**장점:**
- ✅ 한 번의 명령으로 전체 시스템 시작
- ✅ 복잡한 설정 없이 즉시 사용 가능
- ✅ 프로덕션과 유사한 환경

**단계:**

```bash
# 1. 초기 설정 (환경 변수 파일 생성)
make init

# 2. .env 파일 수정 (필요한 경우)
# Stripe API 키 등을 설정하세요
vim .env

# 3. 전체 시스템 시작 + DB 초기화
make dev

# 또는 단계별로:
make up        # 시스템 시작
make init-db   # DynamoDB 테이블 생성
```

**접속:**
- Frontend: http://localhost:3000
- API Gateway: http://localhost:8000
- Docs: http://localhost:8000/docs

**유용한 명령어:**
```bash
make ps                        # 서비스 상태 확인
make logs                      # 전체 로그 확인
make logs service=auth         # 특정 서비스 로그
make restart service=auth      # 서비스 재시작
make down                      # 시스템 중지
make clean                     # 전체 삭제 (데이터 포함)
```

---

## 방법 2: Makefile (수동 제어)

**장점:**
- ✅ 개별 서비스 제어 가능
- ✅ 인프라만 띄우고 일부 서비스는 로컬 실행 가능
- ✅ 리소스 효율적

**단계:**

```bash
# 1. 초기 설정
make init

# 2. 인프라만 시작 (PostgreSQL, Redis, etc.)
make start-infra

# 3. 특정 서비스만 시작
make start service=auth
make start service=api-gateway

# 또는 전체 애플리케이션 시작
make start-services
```

**서비스별 실행 (로컬 개발):**
```bash
# Auth 서비스만 로컬에서 실행
cd services/auth
python -m venv venv
source venv/bin/activate
uv pip install -r pyproject.toml
uvicorn app.main:app --reload --port 8001
```

---

## 방법 3: Tilt + Kubernetes (프로덕션과 동일 환경)

**장점:**
- ✅ 프로덕션과 완전히 동일한 환경
- ✅ 코드 변경 시 자동 재빌드/배포
- ✅ 실시간 로그 스트리밍
- ⚠️ 학습 곡선 있음

**사전 요구사항:**
```bash
# Minikube 설치
brew install minikube kubectl tilt

# Minikube 시작
minikube start --cpus=4 --memory=8192

# Docker 환경 연결
eval $(minikube docker-env)
```

**시작:**
```bash
# Tilt 실행 (자동으로 빌드 + 배포)
tilt up

# Tilt UI 열기 (자동으로 열림)
# http://localhost:10350
```

**Tilt UI에서 할 수 있는 것:**
- 📊 모든 서비스 상태 한눈에 확인
- 📜 실시간 로그 스트리밍
- 🔄 빌드 진행 상황 모니터링
- 🔧 서비스별 재시작/재빌드

**중지:**
```bash
# Tilt 종료
tilt down

# Minikube 중지
minikube stop
```

---

## 🔍 문제 해결

### Docker Compose 포트 충돌
```bash
# 실행 중인 컨테이너 확인
docker ps

# 포트 사용 중인 프로세스 종료 (macOS/Linux)
lsof -ti:8000 | xargs kill -9
```

### DynamoDB 테이블 생성 실패
```bash
# 수동으로 테이블 생성
./scripts/init-dynamodb.sh

# 또는 Docker Compose 재시작
make restart service=dynamodb-local
make init-db
```

### Kubernetes 리소스 정리
```bash
# 네임스페이스 삭제
kubectl delete namespace ticketing-local

# Minikube 완전 재시작
minikube delete
minikube start --cpus=4 --memory=8192
```

### 빌드 캐시 문제
```bash
# Docker Compose: 캐시 없이 재빌드
make rebuild

# Tilt: 빌드 캐시 삭제
tilt down
docker system prune -a
tilt up
```

---

## 📚 다음 단계

1. **테스트 데이터 삽입**
   ```bash
   # TODO: seed 스크립트 추가 예정
   make seed
   ```

2. **API 문서 확인**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

3. **모니터링 (선택 사항)**
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3001

4. **코드 변경 테스트**
   - Docker Compose: 서비스 재시작 필요
   - Tilt: 자동으로 재빌드/배포

---

## 💡 개발 팁

### 효율적인 워크플로우

**옵션 A: Docker Compose + 로컬 서비스**
```bash
# 인프라만 Docker로 실행
make start-infra

# 개발 중인 서비스만 로컬 실행 (hot reload)
cd services/auth
uvicorn app.main:app --reload
```

**옵션 B: Tilt로 모든 것 자동화**
```bash
# 한 번만 실행
tilt up

# 코드 수정 → 저장 → 자동 재배포
# 별도 작업 불필요!
```

### 로그 확인 팁
```bash
# Docker Compose: 특정 서비스 로그만
make logs service=auth | grep ERROR

# Tilt: UI에서 필터링 기능 사용
# http://localhost:10350
```

### 데이터베이스 접속
```bash
# PostgreSQL
docker exec -it ticketing-postgres psql -U ticketing

# Redis
docker exec -it ticketing-redis redis-cli

# DynamoDB Local
aws dynamodb list-tables --endpoint-url http://localhost:8001
```

---

## 🎯 추천 방법

| 상황 | 추천 방법 |
|------|---------|
| 처음 시작 | Docker Compose |
| 빠른 개발 | Docker Compose + 로컬 실행 |
| 프로덕션 테스트 | Tilt + Kubernetes |
| 팀 협업 | Tilt (통일된 환경) |

---

**문제가 있나요?**
- [SETUP.md](./SETUP.md) - 상세한 설정 가이드
- [README.md](./README.md) - 프로젝트 개요
- [GitHub Issues](./issues) - 버그 리포트
