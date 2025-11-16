from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


# Booking schemas
class BookingCreate(BaseModel):
    event_id: str = Field(..., min_length=1)
    seat_number: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)


class BookingConfirm(BaseModel):
    payment_id: str = Field(..., min_length=1)


class BookingResponse(BaseModel):
    booking_id: str
    event_id: str
    seat_number: str
    user_id: str
    status: BookingStatus
    reservation_id: Optional[str] = None
    payment_id: Optional[str] = None
    price: float
    created_at: datetime
    confirmed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BookingListResponse(BaseModel):
    bookings: list[BookingResponse]
    total: int


# Health check
class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime
