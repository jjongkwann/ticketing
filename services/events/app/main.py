import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from app.db import init_db
from app.routers import events
from app.schemas import HealthResponse
from app.search import init_opensearch_index

# Logging configuration
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작 및 종료 시 실행"""
    logger.info("Starting Events Service...")
    await init_db()
    logger.info("Database initialized")

    await init_opensearch_index()
    logger.info("OpenSearch index initialized")

    yield
    logger.info("Shutting down Events Service...")


# FastAPI app
app = FastAPI(
    title="Events Service",
    description="이벤트 관리 및 검색 서비스",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    # Prometheus metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
    ).inc()

    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path,
    ).observe(duration)

    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code} - Duration: {duration:.3f}s")

    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Routers
app.include_router(events.router)


# Health check endpoints
@app.get("/health", response_model=HealthResponse)
async def health():
    """헬스체크"""
    return HealthResponse(
        status="healthy",
        service="events-service",
        timestamp=datetime.utcnow(),
    )


@app.get("/ready", response_model=HealthResponse)
async def ready():
    """레디니스 체크"""
    return HealthResponse(
        status="ready",
        service="events-service",
        timestamp=datetime.utcnow(),
    )


# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus 메트릭"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "Events Service",
        "version": "1.0.0",
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("ENVIRONMENT") != "production",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
