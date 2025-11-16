#!/bin/bash

set -e

echo "========================================"
echo "모니터링 스택 배포 스크립트"
echo "========================================"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 환경 변수 체크
check_env() {
    if [ -z "$DATADOG_API_KEY" ]; then
        echo -e "${RED}Error: DATADOG_API_KEY 환경 변수가 설정되지 않았습니다.${NC}"
        exit 1
    fi

    if [ -z "$DATADOG_APP_KEY" ]; then
        echo -e "${RED}Error: DATADOG_APP_KEY 환경 변수가 설정되지 않았습니다.${NC}"
        exit 1
    fi
}

# Helm 리포지토리 추가
setup_helm_repos() {
    echo -e "${GREEN}[1/6] Helm 리포지토리 추가 중...${NC}"
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts || true
    helm repo add grafana https://grafana.github.io/helm-charts || true
    helm repo update
}

# 네임스페이스 생성
create_namespace() {
    echo -e "${GREEN}[2/6] 네임스페이스 생성 중...${NC}"
    kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
    kubectl create namespace ticketing --dry-run=client -o yaml | kubectl apply -f -
}

# Datadog 배포
deploy_datadog() {
    echo -e "${GREEN}[3/6] Datadog Agent 배포 중...${NC}"

    # Secret 생성
    kubectl create secret generic datadog-secret \
        --from-literal=api-key="$DATADOG_API_KEY" \
        --from-literal=app-key="$DATADOG_APP_KEY" \
        -n ticketing \
        --dry-run=client -o yaml | kubectl apply -f -

    # Datadog Agent 배포
    kubectl apply -f datadog-agent.yaml

    echo -e "${YELLOW}Datadog Agent가 배포되었습니다. 약 1-2분 후 https://app.datadoghq.com 에서 확인하세요.${NC}"
}

# Prometheus Stack 배포
deploy_prometheus() {
    echo -e "${GREEN}[4/6] Prometheus Stack 배포 중...${NC}"

    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
        -n monitoring \
        -f prometheus-values.yaml \
        --wait \
        --timeout 10m

    echo -e "${YELLOW}Prometheus Stack이 배포되었습니다.${NC}"
    echo -e "${YELLOW}Grafana 접속: kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80${NC}"
}

# Loki 배포
deploy_loki() {
    echo -e "${GREEN}[5/6] Loki Stack 배포 중...${NC}"

    # S3 버킷 확인
    BUCKET_NAME="ticketing-loki-chunks"
    if ! aws s3 ls "s3://$BUCKET_NAME" 2>&1 > /dev/null; then
        echo -e "${YELLOW}S3 버킷 생성 중: $BUCKET_NAME${NC}"
        aws s3 mb "s3://$BUCKET_NAME" --region us-east-1
    else
        echo -e "${GREEN}S3 버킷이 이미 존재합니다: $BUCKET_NAME${NC}"
    fi

    helm upgrade --install loki grafana/loki-stack \
        -n monitoring \
        -f loki-values.yaml \
        --wait \
        --timeout 10m

    echo -e "${YELLOW}Loki Stack이 배포되었습니다.${NC}"
}

# ServiceMonitor 배포
deploy_servicemonitors() {
    echo -e "${GREEN}[6/6] ServiceMonitor 배포 중...${NC}"
    kubectl apply -f servicemonitors.yaml
    echo -e "${GREEN}ServiceMonitor가 배포되었습니다.${NC}"
}

# 배포 상태 확인
check_status() {
    echo ""
    echo -e "${GREEN}========================================"
    echo "배포 상태 확인"
    echo "========================================${NC}"

    echo ""
    echo -e "${YELLOW}[Monitoring Namespace]${NC}"
    kubectl get pods -n monitoring

    echo ""
    echo -e "${YELLOW}[Ticketing Namespace - Datadog]${NC}"
    kubectl get pods -n ticketing -l app=datadog-agent

    echo ""
    echo -e "${YELLOW}[ServiceMonitors]${NC}"
    kubectl get servicemonitor -n ticketing

    echo ""
    echo -e "${GREEN}========================================"
    echo "접속 방법"
    echo "========================================${NC}"
    echo ""
    echo "Grafana:"
    echo "  kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80"
    echo "  http://localhost:3000 (admin/admin)"
    echo ""
    echo "Prometheus:"
    echo "  kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090"
    echo "  http://localhost:9090"
    echo ""
    echo "Datadog:"
    echo "  https://app.datadoghq.com"
    echo ""
}

# 메인 실행
main() {
    check_env
    setup_helm_repos
    create_namespace
    deploy_datadog
    deploy_prometheus
    deploy_loki
    deploy_servicemonitors
    check_status

    echo -e "${GREEN}모니터링 스택 배포가 완료되었습니다!${NC}"
}

# 스크립트 실행
main
