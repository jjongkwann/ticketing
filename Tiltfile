# Tiltfile for Ticketing Pro
# Kubernetes 로컬 개발 환경 자동화

# ============================================
# 설정
# ============================================
# Minikube를 사용하는 경우 Docker 환경 설정
allow_k8s_contexts('minikube')

# Kubernetes 네임스페이스 설정
namespace = 'ticketing-local'

# ============================================
# 인프라 서비스 (옵션: 로컬에 이미 실행 중이면 주석 처리)
# ============================================

# PostgreSQL
k8s_yaml('k8s/local/postgres.yaml') if os.path.exists('k8s/local/postgres.yaml') else None
k8s_resource(
    'postgres',
    port_forwards='5432:5432',
    labels=['infrastructure'],
)

# Redis
k8s_yaml('k8s/local/redis.yaml') if os.path.exists('k8s/local/redis.yaml') else None
k8s_resource(
    'redis',
    port_forwards='6379:6379',
    labels=['infrastructure'],
)

# DynamoDB Local
k8s_yaml('k8s/local/dynamodb.yaml') if os.path.exists('k8s/local/dynamodb.yaml') else None
k8s_resource(
    'dynamodb-local',
    port_forwards='8001:8000',
    labels=['infrastructure'],
)

# OpenSearch
k8s_yaml('k8s/local/opensearch.yaml') if os.path.exists('k8s/local/opensearch.yaml') else None
k8s_resource(
    'opensearch',
    port_forwards=['9200:9200', '9600:9600'],
    labels=['infrastructure'],
)

# Kafka
k8s_yaml('k8s/local/kafka.yaml') if os.path.exists('k8s/local/kafka.yaml') else None
k8s_resource(
    'kafka',
    port_forwards='9092:9092',
    labels=['infrastructure'],
)

# ============================================
# 공통 리소스
# ============================================
k8s_yaml('k8s/local/namespace.yaml')
k8s_yaml('k8s/local/configmap.yaml')
k8s_yaml('k8s/local/secrets.yaml')

# ============================================
# 애플리케이션 서비스
# ============================================

# Auth Service
docker_build(
    'ticketing/auth-service:local',
    context='./services/auth',
    dockerfile='./services/auth/Dockerfile',
    live_update=[
        sync('./services/auth/app', '/app/app'),
        run('pip install -e .', trigger='./services/auth/pyproject.toml'),
    ],
)
k8s_yaml('k8s/local/auth-service.yaml')
k8s_resource(
    'auth-service',
    port_forwards='8001:8000',
    labels=['backend'],
    resource_deps=['postgres'],
)

# Events Service
docker_build(
    'ticketing/events-service:local',
    context='./services/events',
    dockerfile='./services/events/Dockerfile',
    live_update=[
        sync('./services/events/app', '/app/app'),
        run('pip install -e .', trigger='./services/events/pyproject.toml'),
    ],
)
k8s_yaml('k8s/local/events-service.yaml') if os.path.exists('k8s/local/events-service.yaml') else None
k8s_resource(
    'events-service',
    port_forwards='8002:8000',
    labels=['backend'],
    resource_deps=['postgres'],
)

# Inventory Service (Go)
docker_build(
    'ticketing/inventory-service:local',
    context='./services/inventory',
    dockerfile='./services/inventory/Dockerfile',
    live_update=[
        sync('./services/inventory', '/app'),
        run('go build -o /app/server ./cmd/server', trigger='./services/inventory/**/*.go'),
    ],
)
k8s_yaml('k8s/local/inventory-service.yaml') if os.path.exists('k8s/local/inventory-service.yaml') else None
k8s_resource(
    'inventory-service',
    port_forwards=['50051:50051', '8080:8080'],
    labels=['backend'],
    resource_deps=['dynamodb-local', 'redis'],
)

# Booking Service
docker_build(
    'ticketing/booking-service:local',
    context='./services/booking',
    dockerfile='./services/booking/Dockerfile',
    live_update=[
        sync('./services/booking/app', '/app/app'),
        run('pip install -e .', trigger='./services/booking/pyproject.toml'),
    ],
)
k8s_yaml('k8s/local/booking-service.yaml') if os.path.exists('k8s/local/booking-service.yaml') else None
k8s_resource(
    'booking-service',
    port_forwards='8003:8000',
    labels=['backend'],
    resource_deps=['dynamodb-local', 'kafka', 'inventory-service'],
)

# Payment Service
docker_build(
    'ticketing/payment-service:local',
    context='./services/payment',
    dockerfile='./services/payment/Dockerfile',
    live_update=[
        sync('./services/payment/app', '/app/app'),
        run('pip install -e .', trigger='./services/payment/pyproject.toml'),
    ],
)
k8s_yaml('k8s/local/payment-service.yaml') if os.path.exists('k8s/local/payment-service.yaml') else None
k8s_resource(
    'payment-service',
    port_forwards='8004:8000',
    labels=['backend'],
    resource_deps=['booking-service'],
)

# Search Service
docker_build(
    'ticketing/search-service:local',
    context='./services/search',
    dockerfile='./services/search/Dockerfile',
    live_update=[
        sync('./services/search/app', '/app/app'),
        run('pip install -e .', trigger='./services/search/pyproject.toml'),
    ],
)
k8s_yaml('k8s/local/search-service.yaml') if os.path.exists('k8s/local/search-service.yaml') else None
k8s_resource(
    'search-service',
    port_forwards='8005:8000',
    labels=['backend'],
    resource_deps=['opensearch'],
)

# Notification Service
docker_build(
    'ticketing/notification-service:local',
    context='./services/notification',
    dockerfile='./services/notification/Dockerfile',
    live_update=[
        sync('./services/notification/app', '/app/app'),
        run('pip install -e .', trigger='./services/notification/pyproject.toml'),
    ],
)
k8s_yaml('k8s/local/notification-service.yaml') if os.path.exists('k8s/local/notification-service.yaml') else None
k8s_resource(
    'notification-service',
    port_forwards='8006:8000',
    labels=['backend'],
    resource_deps=['kafka'],
)

# API Gateway
docker_build(
    'ticketing/api-gateway-service:local',
    context='./services/api-gateway',
    dockerfile='./services/api-gateway/Dockerfile',
    live_update=[
        sync('./services/api-gateway/app', '/app/app'),
        run('pip install -e .', trigger='./services/api-gateway/pyproject.toml'),
    ],
)
k8s_yaml('k8s/local/api-gateway.yaml')
k8s_resource(
    'api-gateway',
    port_forwards='8000:8000',
    labels=['gateway'],
    resource_deps=['auth-service', 'events-service', 'booking-service', 'payment-service', 'search-service'],
)

# Frontend
docker_build(
    'ticketing/frontend:local',
    context='./frontend',
    dockerfile='./frontend/Dockerfile',
    live_update=[
        sync('./frontend/src', '/app/src'),
        run('npm run build', trigger='./frontend/src/**/*'),
    ],
)
k8s_yaml('k8s/local/frontend.yaml') if os.path.exists('k8s/local/frontend.yaml') else None
k8s_resource(
    'frontend',
    port_forwards='3000:80',
    labels=['frontend'],
    resource_deps=['api-gateway'],
)

# ============================================
# Tilt 설정
# ============================================

# 로그 출력 설정
update_settings(max_parallel_updates=3)

# 빌드 최적화
load('ext://restart_process', 'docker_build_with_restart')

print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                                 ║
║              🎫 Ticketing Pro - Tilt 개발 환경                  ║
║                                                                 ║
║  Tilt가 Kubernetes 로컬 개발 환경을 자동으로 관리합니다.          ║
║                                                                 ║
║  📋 주요 기능:                                                  ║
║    • 코드 변경 시 자동 재빌드 및 배포                            ║
║    • 실시간 로그 스트리밍                                        ║
║    • 포트 포워딩 자동 설정                                       ║
║                                                                 ║
║  🌐 접속 정보:                                                  ║
║    • Frontend:    http://localhost:3000                        ║
║    • API Gateway: http://localhost:8000                        ║
║    • Auth:        http://localhost:8001                        ║
║    • Inventory:   http://localhost:50051 (gRPC)                ║
║                                                                 ║
║  💡 팁:                                                         ║
║    • Tilt UI에서 서비스 상태와 로그를 확인하세요                 ║
║    • 코드를 수정하면 자동으로 배포됩니다                         ║
║                                                                 ║
╚═══════════════════════════════════════════════════════════════╝
""")
