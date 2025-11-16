.PHONY: help up down restart build rebuild ps logs clean init \
	start-infra stop-infra start-services stop-services \
	logs-service exec shell test migrate seed

.DEFAULT_GOAL := help

# ============================================
# 색상 정의 (터미널 출력용)
# ============================================
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# ============================================
# 변수
# ============================================
COMPOSE := docker-compose
ENV_FILE := .env
ENV_EXAMPLE := .env.example

# 서비스 그룹
INFRA_SERVICES := postgres redis dynamodb-local opensearch kafka
APP_SERVICES := auth events inventory booking payment search notification api-gateway frontend

# ============================================
# 도움말
# ============================================
help: ## 📖 사용 가능한 명령어 출력
	@echo "$(BLUE)Ticketing Pro - 개발 환경 관리$(NC)"
	@echo ""
	@echo "$(GREEN)주요 명령어:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)예제:$(NC)"
	@echo "  make up                    # 전체 시스템 시작"
	@echo "  make logs service=auth     # Auth 서비스 로그 확인"
	@echo "  make restart service=api-gateway  # API Gateway 재시작"
	@echo "  make exec service=auth cmd='bash'  # Auth 컨테이너 접속"

# ============================================
# 환경 설정
# ============================================
init: ## 🔧 초기 설정 (. env 생성 + DB 초기화)
	@echo "$(BLUE)🔧 초기 설정 시작...$(NC)"
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "$(GREEN)✅ .env 파일 생성 중...$(NC)"; \
		cp $(ENV_EXAMPLE) $(ENV_FILE); \
		echo "$(YELLOW)⚠️  .env 파일을 열어 필요한 값을 설정하세요.$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  .env 파일이 이미 존재합니다.$(NC)"; \
	fi
	@echo "$(GREEN)✅ 초기 설정 완료!$(NC)"
	@echo "$(BLUE)💡 다음 단계: make up$(NC)"

check-env: ## 🔍 .env 파일 확인
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "$(RED)❌ .env 파일이 없습니다. 'make init'를 먼저 실행하세요.$(NC)"; \
		exit 1; \
	fi

# ============================================
# Docker Compose 제어
# ============================================
up: check-env ## 🚀 전체 시스템 시작 (백그라운드)
	@echo "$(BLUE)🚀 Ticketing Pro 시작 중...$(NC)"
	$(COMPOSE) up -d
	@echo ""
	@echo "$(GREEN)✅ 시스템이 시작되었습니다!$(NC)"
	@echo ""
	@echo "$(YELLOW)📋 서비스 상태 확인: make ps$(NC)"
	@echo "$(YELLOW)📋 로그 확인: make logs$(NC)"
	@echo "$(YELLOW)📋 DynamoDB 초기화: make init-db$(NC)"

down: ## 🛑 전체 시스템 중지
	@echo "$(BLUE)🛑 시스템 중지 중...$(NC)"
	$(COMPOSE) down
	@echo "$(GREEN)✅ 시스템이 중지되었습니다.$(NC)"

restart: ## 🔄 전체 시스템 재시작
	@echo "$(BLUE)🔄 시스템 재시작 중...$(NC)"
	$(COMPOSE) restart
	@echo "$(GREEN)✅ 시스템이 재시작되었습니다.$(NC)"

# ============================================
# 서비스 그룹 제어
# ============================================
start-infra: check-env ## 🏗️ 인프라 서비스만 시작 (PostgreSQL, Redis, etc.)
	@echo "$(BLUE)🏗️  인프라 서비스 시작 중...$(NC)"
	$(COMPOSE) up -d $(INFRA_SERVICES)
	@echo "$(GREEN)✅ 인프라 서비스가 시작되었습니다.$(NC)"

stop-infra: ## 🏗️ 인프라 서비스만 중지
	@echo "$(BLUE)🏗️  인프라 서비스 중지 중...$(NC)"
	$(COMPOSE) stop $(INFRA_SERVICES)
	@echo "$(GREEN)✅ 인프라 서비스가 중지되었습니다.$(NC)"

start-services: check-env ## 🎯 애플리케이션 서비스만 시작
	@echo "$(BLUE)🎯 애플리케이션 서비스 시작 중...$(NC)"
	$(COMPOSE) up -d $(APP_SERVICES)
	@echo "$(GREEN)✅ 애플리케이션 서비스가 시작되었습니다.$(NC)"

stop-services: ## 🎯 애플리케이션 서비스만 중지
	@echo "$(BLUE)🎯 애플리케이션 서비스 중지 중...$(NC)"
	$(COMPOSE) stop $(APP_SERVICES)
	@echo "$(GREEN)✅ 애플리케이션 서비스가 중지되었습니다.$(NC)"

# ============================================
# 개별 서비스 제어
# ============================================
start: check-env ## ▶️  특정 서비스 시작 (예: make start service=auth)
ifndef service
	@echo "$(RED)❌ 서비스를 지정하세요: make start service=<서비스명>$(NC)"
	@exit 1
endif
	@echo "$(BLUE)▶️  $(service) 서비스 시작 중...$(NC)"
	$(COMPOSE) up -d $(service)
	@echo "$(GREEN)✅ $(service) 서비스가 시작되었습니다.$(NC)"

stop: ## ⏹️  특정 서비스 중지 (예: make stop service=auth)
ifndef service
	@echo "$(RED)❌ 서비스를 지정하세요: make stop service=<서비스명>$(NC)"
	@exit 1
endif
	@echo "$(BLUE)⏹️  $(service) 서비스 중지 중...$(NC)"
	$(COMPOSE) stop $(service)
	@echo "$(GREEN)✅ $(service) 서비스가 중지되었습니다.$(NC)"

restart-service: ## 🔄 특정 서비스 재시작 (예: make restart-service service=auth)
ifndef service
	@echo "$(RED)❌ 서비스를 지정하세요: make restart-service service=<서비스명>$(NC)"
	@exit 1
endif
	@echo "$(BLUE)🔄 $(service) 서비스 재시작 중...$(NC)"
	$(COMPOSE) restart $(service)
	@echo "$(GREEN)✅ $(service) 서비스가 재시작되었습니다.$(NC)"

# ============================================
# 빌드
# ============================================
build: check-env ## 🔨 전체 이미지 빌드
	@echo "$(BLUE)🔨 이미지 빌드 중...$(NC)"
	$(COMPOSE) build
	@echo "$(GREEN)✅ 빌드 완료!$(NC)"

rebuild: check-env ## 🔨 캐시 없이 전체 재빌드
	@echo "$(BLUE)🔨 캐시 없이 재빌드 중...$(NC)"
	$(COMPOSE) build --no-cache
	@echo "$(GREEN)✅ 재빌드 완료!$(NC)"

build-service: check-env ## 🔨 특정 서비스만 빌드 (예: make build-service service=auth)
ifndef service
	@echo "$(RED)❌ 서비스를 지정하세요: make build-service service=<서비스명>$(NC)"
	@exit 1
endif
	@echo "$(BLUE)🔨 $(service) 서비스 빌드 중...$(NC)"
	$(COMPOSE) build $(service)
	@echo "$(GREEN)✅ $(service) 빌드 완료!$(NC)"

# ============================================
# 로그 & 모니터링
# ============================================
ps: ## 📊 실행 중인 서비스 상태 확인
	@$(COMPOSE) ps

logs: ## 📜 전체 로그 출력 (실시간)
	$(COMPOSE) logs -f

logs-service: ## 📜 특정 서비스 로그 출력 (예: make logs-service service=auth)
ifndef service
	@echo "$(RED)❌ 서비스를 지정하세요: make logs-service service=<서비스명>$(NC)"
	@exit 1
endif
	$(COMPOSE) logs -f $(service)

# ============================================
# 데이터베이스 & 초기화
# ============================================
init-db: ## 🗄️ DynamoDB 테이블 초기화
	@echo "$(BLUE)🗄️  DynamoDB 테이블 초기화 중...$(NC)"
	@./scripts/init-dynamodb.sh
	@echo "$(GREEN)✅ DynamoDB 초기화 완료!$(NC)"

migrate: ## 🔄 PostgreSQL 마이그레이션 실행 (Auth, Events)
	@echo "$(BLUE)🔄 마이그레이션 실행 중...$(NC)"
	@echo "$(YELLOW)Auth Service 마이그레이션...$(NC)"
	$(COMPOSE) exec auth alembic upgrade head || echo "$(YELLOW)⚠️  Auth 마이그레이션 건너뜀$(NC)"
	@echo "$(YELLOW)Events Service 마이그레이션...$(NC)"
	$(COMPOSE) exec events alembic upgrade head || echo "$(YELLOW)⚠️  Events 마이그레이션 건너뜀$(NC)"
	@echo "$(GREEN)✅ 마이그레이션 완료!$(NC)"

seed: ## 🌱 초기 데이터 삽입
	@echo "$(BLUE)🌱 초기 데이터 삽입 중...$(NC)"
	@echo "$(YELLOW)⚠️  seed 스크립트를 구현하세요.$(NC)"

# ============================================
# 개발 도구
# ============================================
exec: ## 🔧 컨테이너 내부 명령 실행 (예: make exec service=auth cmd='bash')
ifndef service
	@echo "$(RED)❌ 서비스를 지정하세요: make exec service=<서비스명> cmd='<명령어>'$(NC)"
	@exit 1
endif
ifndef cmd
	@echo "$(RED)❌ 명령어를 지정하세요: make exec service=<서비스명> cmd='<명령어>'$(NC)"
	@exit 1
endif
	$(COMPOSE) exec $(service) $(cmd)

shell: ## 🐚 컨테이너 쉘 접속 (예: make shell service=auth)
ifndef service
	@echo "$(RED)❌ 서비스를 지정하세요: make shell service=<서비스명>$(NC)"
	@exit 1
endif
	@echo "$(BLUE)🐚 $(service) 컨테이너 접속 중...$(NC)"
	$(COMPOSE) exec $(service) /bin/sh

# ============================================
# 테스트
# ============================================
test: ## 🧪 전체 테스트 실행
	@echo "$(BLUE)🧪 테스트 실행 중...$(NC)"
	@echo "$(YELLOW)⚠️  테스트 스크립트를 구현하세요.$(NC)"

test-service: ## 🧪 특정 서비스 테스트 (예: make test-service service=auth)
ifndef service
	@echo "$(RED)❌ 서비스를 지정하세요: make test-service service=<서비스명>$(NC)"
	@exit 1
endif
	@echo "$(BLUE)🧪 $(service) 테스트 실행 중...$(NC)"
	$(COMPOSE) exec $(service) pytest

# ============================================
# 정리
# ============================================
clean: ## 🧹 모든 컨테이너, 볼륨, 네트워크 삭제
	@echo "$(RED)⚠️  모든 데이터가 삭제됩니다. 계속하시겠습니까? [y/N]$(NC)"
	@read -r answer; \
	if [ "$$answer" = "y" ] || [ "$$answer" = "Y" ]; then \
		echo "$(BLUE)🧹 정리 중...$(NC)"; \
		$(COMPOSE) down -v --remove-orphans; \
		echo "$(GREEN)✅ 정리 완료!$(NC)"; \
	else \
		echo "$(YELLOW)취소되었습니다.$(NC)"; \
	fi

prune: ## 🗑️  사용하지 않는 Docker 리소스 삭제
	@echo "$(BLUE)🗑️  사용하지 않는 Docker 리소스 삭제 중...$(NC)"
	docker system prune -f
	@echo "$(GREEN)✅ 정리 완료!$(NC)"

# ============================================
# 빠른 시작 워크플로우
# ============================================
dev: init up init-db ## 🚀 개발 환경 한번에 시작 (init + up + init-db)
	@echo ""
	@echo "$(GREEN)✅ 개발 환경이 준비되었습니다!$(NC)"
	@echo ""
	@echo "$(BLUE)📋 접속 정보:$(NC)"
	@echo "  Frontend:     http://localhost:3000"
	@echo "  API Gateway:  http://localhost:8000"
	@echo "  Auth:         http://localhost:8001"
	@echo "  Events:       http://localhost:8002"
	@echo "  Booking:      http://localhost:8003"
	@echo "  Payment:      http://localhost:8004"
	@echo "  Search:       http://localhost:8005"
	@echo "  Inventory:    http://localhost:50051 (gRPC)"
	@echo ""
	@echo "$(YELLOW)💡 팁: make logs 로 로그를 확인하세요.$(NC)"
