from fastapi import APIRouter, HTTPException, status, Depends, Request, Header
from typing import Optional
import uuid
from datetime import datetime
import logging
import httpx

from app.schemas import (
    PaymentCreate,
    PaymentIntent,
    PaymentResponse,
    RefundRequest,
    RefundResponse,
    PaymentStatus
)
from app.stripe_service import get_stripe_service

router = APIRouter(prefix="/payments", tags=["payments"])
logger = logging.getLogger(__name__)

# Mock payment storage (in production, use DynamoDB)
payments_db = {}


async def get_current_user_id() -> str:
    """임시 사용자 ID"""
    return "user-123"


@router.post("/create-intent", response_model=PaymentIntent)
async def create_payment_intent(
    payment_data: PaymentCreate,
    user_id: str = Depends(get_current_user_id)
):
    """결제 Intent 생성 (Stripe)"""
    stripe_service = get_stripe_service()

    try:
        # Create Stripe Payment Intent
        result = await stripe_service.create_payment_intent(
            amount=payment_data.amount,
            currency=payment_data.currency,
            metadata={
                "booking_id": payment_data.booking_id,
                "user_id": user_id
            }
        )

        # Store payment record
        payment_id = str(uuid.uuid4())
        payments_db[payment_id] = {
            "payment_id": payment_id,
            "booking_id": payment_data.booking_id,
            "amount": payment_data.amount,
            "currency": payment_data.currency,
            "status": PaymentStatus.PENDING,
            "payment_method": payment_data.payment_method,
            "stripe_payment_intent_id": result["payment_intent_id"],
            "created_at": datetime.utcnow(),
        }

        return PaymentIntent(
            client_secret=result["client_secret"],
            payment_intent_id=result["payment_intent_id"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment creation failed: {str(e)}"
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature")
):
    """Stripe webhook handler"""
    stripe_service = get_stripe_service()

    payload = await request.body()

    try:
        event = stripe_service.verify_webhook_signature(payload, stripe_signature)

        # Handle different event types
        if event["type"] == "payment_intent.succeeded":
            payment_intent = event["data"]["object"]
            logger.info(f"Payment succeeded: {payment_intent['id']}")

            # Update payment status
            for payment_id, payment in payments_db.items():
                if payment["stripe_payment_intent_id"] == payment_intent["id"]:
                    payment["status"] = PaymentStatus.SUCCEEDED
                    payment["completed_at"] = datetime.utcnow()

                    # Notify Booking Service
                    booking_id = payment["booking_id"]
                    await notify_booking_service(booking_id, payment_id)
                    break

        elif event["type"] == "payment_intent.payment_failed":
            payment_intent = event["data"]["object"]
            logger.error(f"Payment failed: {payment_intent['id']}")

            for payment_id, payment in payments_db.items():
                if payment["stripe_payment_intent_id"] == payment_intent["id"]:
                    payment["status"] = PaymentStatus.FAILED
                    break

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: str, user_id: str = Depends(get_current_user_id)):
    """결제 상세 조회"""
    payment = payments_db.get(payment_id)

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    return PaymentResponse(**payment)


@router.post("/{payment_id}/refund", response_model=RefundResponse)
async def refund_payment(
    payment_id: str,
    refund_data: RefundRequest,
    user_id: str = Depends(get_current_user_id)
):
    """결제 환불"""
    stripe_service = get_stripe_service()

    payment = payments_db.get(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    if payment["status"] != PaymentStatus.SUCCEEDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only refund succeeded payments"
        )

    try:
        result = await stripe_service.create_refund(
            payment_intent_id=payment["stripe_payment_intent_id"],
            reason=refund_data.reason
        )

        # Update payment status
        payment["status"] = PaymentStatus.REFUNDED

        return RefundResponse(
            payment_id=payment_id,
            refund_id=result["refund_id"],
            amount=result["amount"],
            status=result["status"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refund failed: {str(e)}"
        )


async def notify_booking_service(booking_id: str, payment_id: str):
    """Booking Service에 결제 완료 알림"""
    booking_service_url = "http://booking-service:8000"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{booking_service_url}/bookings/{booking_id}/confirm",
                json={"payment_id": payment_id}
            )
            response.raise_for_status()
            logger.info(f"Notified Booking Service for booking {booking_id}")

    except Exception as e:
        logger.error(f"Failed to notify Booking Service: {e}")
