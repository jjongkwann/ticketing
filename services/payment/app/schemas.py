from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"


# Payment schemas
class PaymentCreate(BaseModel):
    booking_id: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    payment_method: PaymentMethod = PaymentMethod.CARD


class PaymentIntent(BaseModel):
    client_secret: str
    payment_intent_id: str


class PaymentResponse(BaseModel):
    payment_id: str
    booking_id: str
    amount: float
    currency: str
    status: PaymentStatus
    payment_method: PaymentMethod
    stripe_payment_intent_id: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RefundRequest(BaseModel):
    reason: Optional[str] = None


class RefundResponse(BaseModel):
    payment_id: str
    refund_id: str
    amount: float
    status: str


# Health check
class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime
