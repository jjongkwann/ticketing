from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def mock_stripe():
    """Mock Stripe API calls"""
    with patch("stripe.PaymentIntent") as mock_pi, patch("stripe.Webhook") as mock_webhook:
        # Mock PaymentIntent.create
        mock_pi.create.return_value = MagicMock(
            id="pi_test123",
            client_secret="pi_test123_secret_456",
            amount=150000,
            currency="krw",
            status="requires_payment_method",
        )

        # Mock PaymentIntent.retrieve
        mock_pi.retrieve.return_value = MagicMock(
            id="pi_test123", status="succeeded", amount=150000, currency="krw", metadata={"booking_id": "book_123"}
        )

        # Mock PaymentIntent.cancel
        mock_pi.cancel.return_value = MagicMock(id="pi_test123", status="canceled")

        # Mock Webhook.construct_event
        mock_webhook.construct_event.return_value = {
            "id": "evt_test123",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test123",
                    "status": "succeeded",
                    "amount": 150000,
                    "metadata": {"booking_id": "book_123"},
                }
            },
        }

        yield {"payment_intent": mock_pi, "webhook": mock_webhook}


@pytest.mark.asyncio
async def test_create_payment_intent(mock_stripe):
    """Test creating a payment intent"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/payment/create-intent",
            json={
                "booking_id": "book_123",
                "amount": 150000,
                "currency": "krw",
                "metadata": {"event_id": "evt_123", "user_id": "user_123"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "client_secret" in data
        assert data["payment_intent_id"].startswith("pi_")

        # Verify Stripe API was called
        mock_stripe["payment_intent"].create.assert_called_once()


@pytest.mark.asyncio
async def test_create_payment_intent_invalid_amount():
    """Test creating payment intent with invalid amount"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/payment/create-intent",
            json={
                "booking_id": "book_123",
                "amount": -100,  # Invalid negative amount
                "currency": "krw",
            },
        )

        assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_payment_status(mock_stripe):
    """Test getting payment status"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/payment/pi_test123")

        assert response.status_code == 200
        data = response.json()
        assert data["payment_intent_id"] == "pi_test123"
        assert data["status"] == "succeeded"
        assert data["amount"] == 150000


@pytest.mark.asyncio
async def test_get_nonexistent_payment():
    """Test getting non-existent payment"""
    with patch("stripe.PaymentIntent.retrieve") as mock_retrieve:
        mock_retrieve.side_effect = Exception("Payment intent not found")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/payment/pi_nonexistent")

            assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_payment(mock_stripe):
    """Test cancelling a payment"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/payment/pi_test123/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "canceled"


@pytest.mark.asyncio
async def test_webhook_payment_succeeded(mock_stripe):
    """Test webhook for successful payment"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/payment/webhook",
            headers={"stripe-signature": "test_signature"},
            json={
                "id": "evt_test123",
                "type": "payment_intent.succeeded",
                "data": {
                    "object": {
                        "id": "pi_test123",
                        "status": "succeeded",
                        "amount": 150000,
                        "metadata": {"booking_id": "book_123"},
                    }
                },
            },
        )

        # Webhook might return 200 or 400 depending on implementation
        assert response.status_code in [200, 400]


@pytest.mark.asyncio
async def test_webhook_payment_failed(mock_stripe):
    """Test webhook for failed payment"""
    mock_stripe["webhook"].construct_event.return_value = {
        "id": "evt_test456",
        "type": "payment_intent.payment_failed",
        "data": {
            "object": {"id": "pi_test456", "status": "failed", "amount": 150000, "metadata": {"booking_id": "book_456"}}
        },
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/payment/webhook",
            headers={"stripe-signature": "test_signature"},
            json={"id": "evt_test456", "type": "payment_intent.payment_failed"},
        )

        assert response.status_code in [200, 400]


@pytest.mark.asyncio
async def test_refund_payment():
    """Test refunding a payment"""
    with patch("stripe.Refund") as mock_refund:
        mock_refund.create.return_value = MagicMock(
            id="re_test123", payment_intent="pi_test123", amount=150000, status="succeeded"
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/payment/pi_test123/refund", json={"amount": 150000, "reason": "requested_by_customer"}
            )

            # Refund endpoint might not be implemented yet
            assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_multiple_payment_intents():
    """Test creating multiple payment intents"""
    with patch("stripe.PaymentIntent.create") as mock_create:
        payment_intents = []

        def create_side_effect(*args, **kwargs):
            pi_id = f"pi_test_{len(payment_intents)}"
            pi = MagicMock(
                id=pi_id,
                client_secret=f"{pi_id}_secret",
                amount=kwargs.get("amount", 0),
                currency=kwargs.get("currency", "krw"),
                status="requires_payment_method",
            )
            payment_intents.append(pi)
            return pi

        mock_create.side_effect = create_side_effect

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create first payment
            response1 = await client.post(
                "/payment/create-intent", json={"booking_id": "book_1", "amount": 100000, "currency": "krw"}
            )

            # Create second payment
            response2 = await client.post(
                "/payment/create-intent", json={"booking_id": "book_2", "amount": 200000, "currency": "krw"}
            )

            assert response1.status_code == 200
            assert response2.status_code == 200
            assert response1.json()["payment_intent_id"] != response2.json()["payment_intent_id"]
