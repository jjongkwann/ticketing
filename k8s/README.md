# Kubernetes Manifests - Ticketing System

EKS 기반 마이크로서비스 배포 매니페스트입니다.

## 디렉토리 구조

```
k8s/
├── base/               # 기본 리소스
│   ├── namespace.yaml        # ticketing, ticketing-dev 네임스페이스
│   ├── configmap.yaml        # 환경 설정
│   ├── serviceaccount.yaml   # IRSA 연동 서비스 계정
│   └── networkpolicy.yaml    # 네트워크 보안 정책
├── services/           # 마이크로서비스 배포
│   ├── inventory-service.yaml    # Go + gRPC (5-50 replicas)
│   ├── auth-service.yaml         # FastAPI (3-20 replicas)
│   ├── events-service.yaml       # FastAPI (3-15 replicas)
│   ├── booking-service.yaml      # FastAPI (5-30 replicas)
│   ├── payment-service.yaml      # FastAPI (3-20 replicas)
│   ├── search-service.yaml       # FastAPI (2-10 replicas)
│   ├── notification-service.yaml # FastAPI (2-10 replicas)
│   └── api-gateway.yaml          # FastAPI (3-20 replicas)
├── ingress/            # 인그레스 설정
│   └── ingress.yaml              # ALB 인그레스 (public + internal)
└── monitoring/         # 모니터링 스택 (별도 구성)
```

## 사전 요구사항

### 1. EKS 클러스터 접근

```bash
# Terraform으로 EKS 생성 후
aws eks update-kubeconfig --region us-east-1 --name ticketing-prod
```

### 2. AWS Load Balancer Controller 설치

```bash
# Helm으로 설치
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=ticketing-prod \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

### 3. Secrets 생성

Terraform으로 생성된 AWS Secrets Manager의 값을 Kubernetes Secret으로 동기화:

```bash
# RDS 자격증명
kubectl create secret generic rds-credentials \
  --from-literal=username=admin \
  --from-literal=password=$(aws secretsmanager get-secret-value --secret-id ticketing-rds-password --query SecretString --output text) \
  -n ticketing

# OpenSearch 자격증명
kubectl create secret generic opensearch-credentials \
  --from-literal=username=admin \
  --from-literal=password=$(aws secretsmanager get-secret-value --secret-id ticketing-opensearch-password --query SecretString --output text) \
  -n ticketing

# Auth Service JWT Secret
kubectl create secret generic auth-secrets \
  --from-literal=jwt-secret=$(openssl rand -base64 32) \
  -n ticketing

# Payment Service Stripe Key
kubectl create secret generic payment-secrets \
  --from-literal=stripe-api-key=sk_live_xxxxxxxxxxxxxxxx \
  -n ticketing
```

## 배포 순서

### 1. 기본 리소스 배포

```bash
# 네임스페이스 생성
kubectl apply -f k8s/base/namespace.yaml

# ConfigMap 업데이트 (Terraform 출력값으로)
# REDIS_ENDPOINT, MSK_BOOTSTRAP_SERVERS 등을 실제 값으로 교체
kubectl apply -f k8s/base/configmap.yaml

# 서비스 계정 생성 (IRSA)
kubectl apply -f k8s/base/serviceaccount.yaml

# 네트워크 정책 적용
kubectl apply -f k8s/base/networkpolicy.yaml
```

### 2. 마이크로서비스 배포

```bash
# 모든 서비스 배포
kubectl apply -f k8s/services/

# 또는 개별 배포
kubectl apply -f k8s/services/inventory-service.yaml
kubectl apply -f k8s/services/auth-service.yaml
kubectl apply -f k8s/services/events-service.yaml
kubectl apply -f k8s/services/booking-service.yaml
kubectl apply -f k8s/services/payment-service.yaml
kubectl apply -f k8s/services/search-service.yaml
kubectl apply -f k8s/services/notification-service.yaml
kubectl apply -f k8s/services/api-gateway.yaml
```

### 3. 인그레스 배포

```bash
# ACM 인증서 ARN, 보안 그룹 ID, WAF ACL ARN 업데이트 후
kubectl apply -f k8s/ingress/ingress.yaml
```

## ConfigMap 업데이트

Terraform 적용 후 실제 엔드포인트로 ConfigMap을 업데이트해야 합니다:

```bash
# Terraform 출력값 확인
cd terraform
terraform output

# ConfigMap 편집
kubectl edit configmap ticketing-config -n ticketing

# 또는 새로운 값으로 적용
kubectl apply -f k8s/base/configmap.yaml
```

업데이트할 값:
- `REDIS_ENDPOINT`: ElastiCache 엔드포인트
- `MSK_BOOTSTRAP_SERVERS`: MSK 브로커 리스트
- `OPENSEARCH_ENDPOINT`: OpenSearch 도메인 엔드포인트
- `RDS_ENDPOINT`: RDS MySQL 엔드포인트

## 배포 확인

```bash
# Pod 상태 확인
kubectl get pods -n ticketing

# Service 확인
kubectl get svc -n ticketing

# Ingress 확인 (ALB 생성 확인)
kubectl get ingress -n ticketing
kubectl describe ingress ticketing-ingress -n ticketing

# HPA 상태 확인
kubectl get hpa -n ticketing

# 로그 확인
kubectl logs -f deployment/inventory-service -n ticketing
```

## 리소스 스펙

### Inventory Service (Go + gRPC)
- **요청**: CPU 500m, Memory 512Mi
- **제한**: CPU 2000m, Memory 2Gi
- **Replicas**: 5-50 (HPA)
- **Node**: inventory 노드 그룹 (taint 적용)

### 기타 FastAPI Services
- **요청**: CPU 200-300m, Memory 256-512Mi
- **제한**: CPU 1000-1500m, Memory 1-2Gi
- **Replicas**: 2-30 (서비스별 상이)
- **Node**: general 노드 그룹

## 모니터링

Prometheus 메트릭은 각 서비스의 `:9090/metrics` 엔드포인트에서 수집됩니다.

```bash
# 메트릭 확인 (포트 포워딩)
kubectl port-forward svc/inventory-service 9090:9090 -n ticketing
curl http://localhost:9090/metrics
```

## 롤링 업데이트

```bash
# 이미지 업데이트
kubectl set image deployment/inventory-service \
  inventory=ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ticketing/inventory-service:v1.2.0 \
  -n ticketing

# 롤아웃 상태 확인
kubectl rollout status deployment/inventory-service -n ticketing

# 롤백 (필요시)
kubectl rollout undo deployment/inventory-service -n ticketing
```

## 스케일링

HPA가 자동으로 스케일링하지만, 수동 조정도 가능합니다:

```bash
# 수동 스케일
kubectl scale deployment inventory-service --replicas=10 -n ticketing

# HPA 일시 중지
kubectl patch hpa inventory-service-hpa -n ticketing -p '{"spec":{"minReplicas":10,"maxReplicas":10}}'
```

## 주의사항

1. **IRSA (IAM Roles for Service Accounts)**: ServiceAccount의 `role-arn` annotation을 실제 IAM Role ARN으로 교체해야 합니다.

2. **ECR 이미지**: 모든 `ACCOUNT_ID`를 실제 AWS 계정 ID로 교체해야 합니다.

3. **인증서**: Ingress의 ACM 인증서 ARN을 실제 값으로 교체해야 합니다.

4. **보안 그룹**: Ingress의 Security Group ID를 실제 값으로 교체해야 합니다.

5. **ConfigMap 업데이트**: Pod 재시작이 필요합니다:
   ```bash
   kubectl rollout restart deployment/inventory-service -n ticketing
   ```

## 트러블슈팅

### Pod가 Pending 상태
```bash
kubectl describe pod <pod-name> -n ticketing
# 노드 리소스, 테인트, 어피니티 확인
```

### Service 연결 실패
```bash
kubectl exec -it <pod-name> -n ticketing -- curl http://inventory-service:8080/health
# 네트워크 정책, 서비스 설정 확인
```

### ALB 생성 안됨
```bash
kubectl logs -n kube-system deployment/aws-load-balancer-controller
# AWS Load Balancer Controller 로그 확인
```
