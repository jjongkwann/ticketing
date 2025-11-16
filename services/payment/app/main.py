from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from datetime import datetime
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
import os
import logging

from app.routers import payment
from app.schemas import HealthResponse

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
REQUEST_DURATION = Histogram("http_request_duration_seconds", "HTTP request duration in seconds", ["method", "endpoint"])

app = FastAPI(title="Payment Service", description="결제 처리 서비스", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=response.status_code).inc()
    REQUEST_DURATION.labels(method=request.method, endpoint=request.url.path).observe(duration)
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code} - Duration: {duration:.3f}s")
    return response


app.include_router(payment.router)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="healthy", service="payment-service", timestamp=datetime.utcnow())


@app.get("/ready", response_model=HealthResponse)
async def ready():
    return HealthResponse(status="ready", service="payment-service", timestamp=datetime.utcnow())


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def root():
    return {"service": "Payment Service", "version": "1.0.0", "status": "running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=os.getenv("ENVIRONMENT") != "production", log_level=os.getenv("LOG_LEVEL", "info").lower())
