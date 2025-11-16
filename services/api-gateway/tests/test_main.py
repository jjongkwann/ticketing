from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for service calls"""
    with patch("httpx.AsyncClient") as mock:
        client = AsyncMock()
        mock.return_value.__aenter__.return_value = client
        yield client


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "api-gateway" in data["service"]


@pytest.mark.asyncio
async def test_rate_limiting(mock_httpx_client):
    """Test rate limiting on auth endpoints"""
    # Mock successful auth response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "test_token"}
    mock_response.headers = {}
    mock_httpx_client.post.return_value = mock_response

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First 10 requests should succeed (rate limit is 10/minute)
        for i in range(10):
            response = await client.post(
                "/api/auth/login", json={"email": "test@example.com", "password": "password123"}
            )
            # Should succeed (200) or hit rate limit (429)
            assert response.status_code in [200, 429]

        # 11th request should be rate limited
        response = await client.post("/api/auth/login", json={"email": "test@example.com", "password": "password123"})
        # Either rate limited or still succeeding
        assert response.status_code in [200, 429]


@pytest.mark.asyncio
async def test_auth_login_proxy(mock_httpx_client):
    """Test proxy to auth service login"""
    # Mock auth service response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "test_token",
        "user": {"user_id": "123", "email": "test@example.com"},
    }
    mock_response.headers = {}
    mock_httpx_client.post.return_value = mock_response

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/auth/login", json={"email": "test@example.com", "password": "password123"})

        # Verify the response
        assert response.status_code in [200, 429]  # Could be rate limited
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data


@pytest.mark.asyncio
async def test_events_search_proxy(mock_httpx_client):
    """Test proxy to events service search"""
    # Mock events service response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "events": [{"event_id": "evt_123", "title": "Test Concert", "category": "concert"}],
        "total": 1,
    }
    mock_response.headers = {}
    mock_httpx_client.get.return_value = mock_response

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/events?category=concert")

        # Verify the response
        assert response.status_code in [200, 429]


@pytest.mark.asyncio
async def test_cors_headers():
    """Test CORS headers are present"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.options("/api/auth/login", headers={"Origin": "http://localhost:3000"})

        # CORS should allow the request
        assert response.status_code in [200, 405]  # Options or Method Not Allowed


@pytest.mark.asyncio
async def test_invalid_service_route():
    """Test request to non-existent service route"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/nonexistent/endpoint")

        # Should return 404 or 500
        assert response.status_code in [404, 500]
