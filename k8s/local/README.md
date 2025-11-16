# 로컬 Kubernetes 개발 가이드

로컬 환경에서 Kubernetes로 서비스를 실행하는 방법입니다.

## 사전 요구사항

### 1. Kubernetes 클러스터

다음 중 하나를 선택:

#### Minikube (권장)
```bash
# 설치
brew install minikube

# 시작
minikube start --cpus=4 --memory=8192

# Docker 환경 연결 (로컬 이미지 사용)
eval $(minikube docker-env)
```

#### Docker Desktop
```bash
# Docker Desktop 설정 > Kubernetes > Enable Kubernetes 체크
# 재시작
```

### 2. kubectl 설치
```bash
brew install kubectl
```

## 빠른 시작

### 1. Docker 이미지 빌드

```bash
# Minikube 사용 시 Docker 환경 연결
eval $(minikube docker-env)

# 각 서비스 이미지 빌드
cd services/api-gateway
docker build -t ticketing/api-gateway:local .

cd ../auth
docker build -t ticketing/auth-service:local .

cd ../events
docker build -t ticketing/events-service:local .

cd ../booking
docker build -t ticketing/booking-service:local .

cd ../payment
docker build -t ticketing/payment-service:local .

cd ../search
docker build -t ticketing/search-service:local .

cd ../notification
docker build -t ticketing/notification-service:local .

cd ../inventory
docker build -t ticketing/inventory-service:local .

cd ../..
```

### 2. 인프라 서비스 실행

```bash
# PostgreSQL
kubectl create namespace ticketing-local
kubectl run postgres --image=postgres:14 \
  --env="POSTGRES_PASSWORD=postgres" \
  --env="POSTGRES_DB=ticketing" \
  --port=5432 \
  -n ticketing-local

kubectl expose pod postgres --port=5432 -n ticketing-local

# Redis
kubectl run redis --image=redis:7-alpine --port=6379 -n ticketing-local
kubectl expose pod redis --port=6379 -n ticketing-local

# Kafka (간단한 single-node)
kubectl run kafka --image=apache/kafka:latest \
  --env="KAFKA_NODE_ID=1" \
  --env="KAFKA_PROCESS_ROLES=broker,controller" \
  --env="KAFKA_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093" \
  --env="KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092" \
  --env="KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER" \
  --env="KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT" \
  --env="KAFKA_CONTROLLER_QUORUM_VOTERS=1@kafka:9093" \
  --port=9092 \
  -n ticketing-local

kubectl expose pod kafka --port=9092 -n ticketing-local

# OpenSearch
kubectl run opensearch --image=opensearchproject/opensearch:latest \
  --env="discovery.type=single-node" \
  --env="DISABLE_SECURITY_PLUGIN=true" \
  --port=9200 \
  -n ticketing-local

kubectl expose pod opensearch --port=9200 -n ticketing-local
```

### 3. 애플리케이션 배포

```bash
# ConfigMap과 Secret 생성
kubectl apply -f k8s/local/namespace.yaml
kubectl apply -f k8s/local/configmap.yaml
kubectl apply -f k8s/local/secrets.yaml

# 서비스 배포
kubectl apply -f k8s/local/api-gateway.yaml
kubectl apply -f k8s/local/auth-service.yaml
# ... 다른 서비스들도 동일하게

# 또는 한번에
kubectl apply -f k8s/local/
```

### 4. 서비스 접근

```bash
# API Gateway 접근
# Minikube
minikube service api-gateway -n ticketing-local

# Docker Desktop
kubectl port-forward svc/api-gateway 8000:8000 -n ticketing-local

# 브라우저에서 http://localhost:8000 접속
```

## 상태 확인

```bash
# Pod 상태
kubectl get pods -n ticketing-local

# 로그 확인
kubectl logs -f deployment/api-gateway -n ticketing-local

# 서비스 확인
kubectl get svc -n ticketing-local
```

## 개발 워크플로우

### 코드 변경 후 재배포

```bash
# 1. 이미지 다시 빌드
cd services/api-gateway
docker build -t ticketing/api-gateway:local .

# 2. Pod 재시작
kubectl rollout restart deployment/api-gateway -n ticketing-local

# 3. 상태 확인
kubectl rollout status deployment/api-gateway -n ticketing-local
```

### 디버깅

```bash
# Pod 내부 접속
kubectl exec -it deployment/api-gateway -n ticketing-local -- /bin/sh

# 환경 변수 확인
kubectl exec deployment/api-gateway -n ticketing-local -- env | grep -i database

# 다른 서비스 연결 테스트
kubectl exec deployment/api-gateway -n ticketing-local -- \
  curl http://auth-service:8000/health
```

## 정리

```bash
# 모든 리소스 삭제
kubectl delete namespace ticketing-local

# Minikube 종료
minikube stop

# Minikube 삭제
minikube delete
```

## Skaffold로 자동화 (선택사항)

더 편리한 개발을 위해 Skaffold 사용:

```bash
# Skaffold 설치
brew install skaffold

# skaffold.yaml 파일 생성 후
skaffold dev

# 코드 변경 시 자동으로 빌드 및 재배포
```

## 프로덕션 배포

프로덕션 배포는 `k8s/services/` 디렉토리의 manifest를 사용:

```bash
kubectl apply -f k8s/base/
kubectl apply -f k8s/services/
kubectl apply -f k8s/ingress/
```

자세한 내용은 [k8s/README.md](../README.md) 참고
