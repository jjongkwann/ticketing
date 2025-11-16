# 모니터링 스택 - Ticketing System

Datadog, Prometheus, Grafana, Loki를 포함한 완전한 관측성(Observability) 스택입니다.

## 구성 요소

### 1. Datadog
- **APM (Application Performance Monitoring)**: 분산 추적, 프로파일링
- **로그 수집**: 모든 Pod 로그 자동 수집
- **메트릭**: 인프라 및 커스텀 메트릭
- **프로세스 모니터링**: 컨테이너 프로세스 가시성

### 2. Prometheus Stack
- **Prometheus**: 시계열 메트릭 데이터베이스
- **Grafana**: 대시보드 및 시각화
- **Alertmanager**: 알림 관리
- **Node Exporter**: 노드 메트릭 수집
- **Kube State Metrics**: Kubernetes 리소스 메트릭

### 3. Loki
- **로그 집계**: 중앙 집중식 로그 저장소
- **Promtail**: 로그 수집 에이전트
- **S3 백엔드**: 장기 로그 저장

## 배포 순서

### 1. Helm 리포지토리 추가

```bash
# Prometheus Stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

# Loki Stack
helm repo add grafana https://grafana.github.io/helm-charts

# 리포지토리 업데이트
helm repo update
```

### 2. Monitoring 네임스페이스 생성

```bash
kubectl create namespace monitoring
```

### 3. Datadog Agent 배포

먼저 Datadog API 키와 App 키를 획득하세요:
- https://app.datadoghq.com/organization-settings/api-keys

```bash
# Secret에 실제 키 설정
kubectl create secret generic datadog-secret \
  --from-literal=api-key=YOUR_DATADOG_API_KEY \
  --from-literal=app-key=YOUR_DATADOG_APP_KEY \
  -n ticketing

# Datadog Agent 배포
kubectl apply -f k8s/monitoring/datadog-agent.yaml
```

### 4. Prometheus Stack 배포

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring \
  -f k8s/monitoring/prometheus-values.yaml
```

### 5. Loki Stack 배포

먼저 S3 버킷을 생성하세요:
```bash
aws s3 mb s3://ticketing-loki-chunks --region us-east-1
```

IAM 정책 생성 및 ServiceAccount에 연결:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::ticketing-loki-chunks",
        "arn:aws:s3:::ticketing-loki-chunks/*"
      ]
    }
  ]
}
```

Loki 배포:
```bash
helm install loki grafana/loki-stack \
  -n monitoring \
  -f k8s/monitoring/loki-values.yaml
```

### 6. ServiceMonitor 배포

```bash
kubectl apply -f k8s/monitoring/servicemonitors.yaml
```

## 접근 방법

### Grafana 대시보드

```bash
# 포트 포워딩
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# 브라우저에서 http://localhost:3000 접속
# 기본 로그인: admin / admin (변경 권장)
```

### Prometheus UI

```bash
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090

# http://localhost:9090
```

### Alertmanager

```bash
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-alertmanager 9093:9093

# http://localhost:9093
```

### Datadog

Datadog 콘솔에서 직접 확인:
- https://app.datadoghq.com/

## 주요 메트릭

### Inventory Service (Go)

```promql
# Request rate
rate(http_requests_total{service="inventory-service"}[5m])

# Error rate
rate(http_requests_total{service="inventory-service",status=~"5.."}[5m])

# Latency (p99)
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{service="inventory-service"}[5m]))

# gRPC metrics
rate(grpc_server_handled_total{service="inventory-service"}[5m])
```

### DynamoDB 연산

```promql
# DynamoDB read/write latency
histogram_quantile(0.99, rate(dynamodb_operation_duration_seconds_bucket[5m]))

# DynamoDB throttled requests
rate(dynamodb_throttled_requests_total[5m])
```

### Redis 연산

```promql
# Redis command latency
histogram_quantile(0.99, rate(redis_command_duration_seconds_bucket[5m]))

# Redis connection pool
redis_connection_pool_active_connections
```

## 알림 규칙

### Critical Alerts

Prometheus Alertmanager에서 자동으로 다음 알림을 생성합니다:

1. **High Error Rate**: 에러율 > 5%
2. **High Latency**: P99 latency > 500ms
3. **Pod Crash**: Pod가 반복적으로 재시작
4. **High Memory**: 메모리 사용률 > 90%
5. **High CPU**: CPU 사용률 > 85%
6. **DynamoDB Throttling**: 초당 10회 이상 throttle

### Slack 통합

Alertmanager에 Slack Webhook 추가:

```yaml
# alertmanager-config.yaml
global:
  slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'

route:
  receiver: 'slack-notifications'
  group_by: ['alertname', 'cluster', 'service']

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - channel: '#ticketing-alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

적용:
```bash
kubectl create secret generic alertmanager-config \
  --from-file=alertmanager.yaml=alertmanager-config.yaml \
  -n monitoring
```

## 대시보드

### Grafana에서 제공되는 기본 대시보드

1. **Kubernetes Cluster Overview** (ID: 7249)
   - 클러스터 전체 리소스 현황
   - 노드별 CPU/메모리 사용률
   - Pod 상태 및 분포

2. **Kubernetes Pods** (ID: 6417)
   - Pod별 상세 메트릭
   - 컨테이너 리소스 사용량
   - 네트워크 I/O

3. **Go Metrics** (ID: 10826)
   - Inventory Service용
   - Goroutine 수
   - GC 메트릭
   - 힙 메모리 사용량

### 커스텀 대시보드

`TODO/grafana-dashboards/` 폴더에 추가 대시보드를 생성할 수 있습니다:

```bash
# 대시보드 JSON을 ConfigMap으로 로드
kubectl create configmap custom-dashboards \
  --from-file=TODO/grafana-dashboards/ \
  -n monitoring
```

## 로그 쿼리 (Loki)

### LogQL 예제

```logql
# 특정 서비스의 에러 로그
{namespace="ticketing", app="inventory-service"} |= "ERROR"

# 느린 쿼리 찾기
{namespace="ticketing"} |= "slow query" | json | duration > 1s

# 특정 시간대의 모든 로그
{namespace="ticketing"} | __timestamp__ >= "2024-01-01T00:00:00Z"

# HTTP 5xx 에러
{namespace="ticketing", app="api-gateway"} |~ "status=[5][0-9][0-9]"
```

## Datadog APM 통합

각 서비스에 Datadog 트레이서를 추가:

### Go (Inventory Service)

```go
import "gopkg.in/DataDog/dd-trace-go.v1/ddtrace/tracer"

func main() {
    tracer.Start(
        tracer.WithEnv("production"),
        tracer.WithService("inventory-service"),
        tracer.WithAgentAddr("localhost:8126"),
    )
    defer tracer.Stop()
}
```

### Python (FastAPI Services)

```python
from ddtrace import tracer
from ddtrace.contrib.fastapi import patch

patch()

@app.middleware("http")
async def add_datadog_trace(request: Request, call_next):
    with tracer.trace("http.request", service="auth-service"):
        response = await call_next(request)
    return response
```

## 비용 최적화

### Prometheus 보존 기간 조정

```yaml
# prometheus-values.yaml
prometheus:
  prometheusSpec:
    retention: 15d  # 30d -> 15d (50% 절감)
```

### Loki 보존 기간 조정

```yaml
# loki-values.yaml
loki:
  config:
    limits_config:
      retention_period: 360h  # 15 days
```

### 메트릭 샘플링

```yaml
# prometheus-values.yaml
prometheus:
  prometheusSpec:
    additionalScrapeConfigs:
      - job_name: 'kubernetes-pods'
        scrape_interval: 30s  # 15s -> 30s
```

## 트러블슈팅

### Prometheus가 메트릭을 수집하지 않음

```bash
# ServiceMonitor 확인
kubectl get servicemonitor -n ticketing

# Prometheus 타겟 확인
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# http://localhost:9090/targets
```

### Datadog Agent가 로그를 전송하지 않음

```bash
# Datadog Agent 로그 확인
kubectl logs -n ticketing daemonset/datadog-agent

# Agent 상태 확인
kubectl exec -it -n ticketing daemonset/datadog-agent -- agent status
```

### Loki가 S3에 쓰지 못함

```bash
# Loki 로그 확인
kubectl logs -n monitoring deployment/loki

# IAM 권한 확인
kubectl describe sa loki -n monitoring
```

## 모니터링 체크리스트

- [ ] Datadog API 키 설정
- [ ] Prometheus 배포 확인
- [ ] Grafana 대시보드 접근 확인
- [ ] Loki S3 버킷 생성 및 IAM 권한 설정
- [ ] ServiceMonitor 생성 확인
- [ ] 알림 채널 (Slack) 설정
- [ ] 기본 대시보드 로드 확인
- [ ] 각 서비스에서 메트릭 엔드포인트 노출 확인
- [ ] Datadog APM 트레이서 통합
