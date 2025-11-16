import logging
import os
from typing import Optional

import stripe

logger = logging.getLogger(__name__)


class StripeService:
    """Stripe payment processing service"""

    def __init__(self):
        stripe.api_key = os.getenv("STRIPE_API_KEY", "")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    async def create_payment_intent(self, amount: float, currency: str, metadata: dict) -> dict:
        """Create Stripe Payment Intent"""
        try:
            # Stripe expects amount in cents
            amount_cents = int(amount * 100)

            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                metadata=metadata,
                automatic_payment_methods={"enabled": True},
            )

            logger.info(f"Created Stripe Payment Intent: {payment_intent.id}")

            return {
                "payment_intent_id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "status": payment_intent.status,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            raise Exception(f"Stripe payment failed: {str(e)}")

    async def retrieve_payment_intent(self, payment_intent_id: str) -> dict:
        """Retrieve Stripe Payment Intent"""
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return {
                "id": payment_intent.id,
                "status": payment_intent.status,
                "amount": payment_intent.amount / 100,  # Convert back to dollars
                "currency": payment_intent.currency.upper(),
                "metadata": payment_intent.metadata,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            raise Exception(f"Failed to retrieve payment: {str(e)}")

    async def confirm_payment_intent(self, payment_intent_id: str) -> dict:
        """Confirm Stripe Payment Intent"""
        try:
            payment_intent = stripe.PaymentIntent.confirm(payment_intent_id)

            return {
                "id": payment_intent.id,
                "status": payment_intent.status,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            raise Exception(f"Failed to confirm payment: {str(e)}")

    async def create_refund(
        self, payment_intent_id: str, amount: Optional[float] = None, reason: Optional[str] = None
    ) -> dict:
        """Create Stripe refund"""
        try:
            refund_params = {"payment_intent": payment_intent_id}

            if amount:
                refund_params["amount"] = int(amount * 100)

            if reason:
                refund_params["reason"] = reason

            refund = stripe.Refund.create(**refund_params)

            logger.info(f"Created Stripe refund: {refund.id}")

            return {
                "refund_id": refund.id,
                "status": refund.status,
                "amount": refund.amount / 100,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            raise Exception(f"Failed to create refund: {str(e)}")

    def verify_webhook_signature(self, payload: bytes, signature: str) -> dict:
        """Verify Stripe webhook signature"""
        try:
            event = stripe.Webhook.construct_event(payload, signature, self.webhook_secret)
            return event

        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            raise Exception("Invalid payload")

        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            raise Exception("Invalid signature")


# Global instance
_stripe_service: Optional[StripeService] = None


def get_stripe_service() -> StripeService:
    """Get Stripe service instance"""
    global _stripe_service

    if _stripe_service is None:
        _stripe_service = StripeService()

    return _stripe_service
