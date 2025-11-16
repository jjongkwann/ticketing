from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import httpx
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="API Gateway", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service endpoints
SERVICES = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000"),
    "events": os.getenv("EVENTS_SERVICE_URL", "http://events-service:8000"),
    "booking": os.getenv("BOOKING_SERVICE_URL", "http://booking-service:8000"),
    "payment": os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8000"),
    "search": os.getenv("SEARCH_SERVICE_URL", "http://search-service:8000"),
}

async def proxy_request(service: str, path: str, request: Request):
    """프록시 요청 처리"""
    service_url = SERVICES.get(service)
    if not service_url:
        raise HTTPException(status_code=404, detail="Service not found")

    url = f"{service_url}{path}"
    headers = dict(request.headers)
    headers.pop("host", None)

    async with httpx.AsyncClient() as client:
        try:
            if request.method == "GET":
                response = await client.get(url, headers=headers, params=request.query_params)
            elif request.method == "POST":
                body = await request.body()
                response = await client.post(url, headers=headers, content=body)
            elif request.method == "PUT":
                body = await request.body()
                response = await client.put(url, headers=headers, content=body)
            elif request.method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")

            return JSONResponse(
                content=response.json() if response.text else {},
                status_code=response.status_code
            )
        except httpx.RequestError as e:
            logger.error(f"Service error: {e}")
            raise HTTPException(status_code=503, detail="Service unavailable")

# Auth routes
@app.post("/api/auth/register")
@limiter.limit("5/minute")
async def auth_register(request: Request):
    return await proxy_request("auth", "/auth/register", request)

@app.post("/api/auth/login")
@limiter.limit("10/minute")
async def auth_login(request: Request):
    return await proxy_request("auth", "/auth/login", request)

@app.get("/api/auth/me")
@limiter.limit("30/minute")
async def auth_me(request: Request):
    return await proxy_request("auth", "/auth/me", request)

# Events routes
@app.get("/api/events")
@limiter.limit("100/minute")
async def events_list(request: Request):
    return await proxy_request("events", "/events", request)

@app.post("/api/events")
@limiter.limit("10/minute")
async def events_create(request: Request):
    return await proxy_request("events", "/events", request)

@app.get("/api/events/{event_id}")
@limiter.limit("100/minute")
async def events_get(event_id: str, request: Request):
    return await proxy_request("events", f"/events/{event_id}", request)

# Search routes
@app.get("/api/search/events")
@limiter.limit("50/minute")
async def search_events(request: Request):
    return await proxy_request("search", "/search/events", request)

# Booking routes
@app.post("/api/bookings")
@limiter.limit("20/minute")
async def bookings_create(request: Request):
    return await proxy_request("booking", "/bookings", request)

@app.get("/api/bookings/my")
@limiter.limit("30/minute")
async def bookings_my(request: Request):
    return await proxy_request("booking", "/bookings/my", request)

@app.post("/api/bookings/{booking_id}/confirm")
@limiter.limit("10/minute")
async def bookings_confirm(booking_id: str, request: Request):
    return await proxy_request("booking", f"/bookings/{booking_id}/confirm", request)

# Payment routes
@app.post("/api/payments/create-intent")
@limiter.limit("20/minute")
async def payments_create_intent(request: Request):
    return await proxy_request("payment", "/payments/create-intent", request)

@app.post("/api/payments/webhook")
async def payments_webhook(request: Request):
    """Stripe webhook - no rate limit"""
    return await proxy_request("payment", "/payments/webhook", request)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "api-gateway", "timestamp": datetime.utcnow().isoformat()}

@app.get("/")
async def root():
    return {
        "service": "API Gateway",
        "version": "1.0.0",
        "services": list(SERVICES.keys())
    }
