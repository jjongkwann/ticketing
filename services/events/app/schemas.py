from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from app.models import EventStatus


# Event schemas
class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    venue: str = Field(..., min_length=1, max_length=255)
    address: str
    start_time: datetime
    end_time: datetime
    total_seats: int = Field(..., gt=0)
    price: Decimal = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=3)
    category: Optional[str] = None
    tags: Optional[str] = None
    image_url: Optional[str] = None
    is_featured: bool = False


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    venue: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_seats: Optional[int] = Field(None, gt=0)
    price: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    status: Optional[EventStatus] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    image_url: Optional[str] = None
    is_featured: Optional[bool] = None


class EventInDB(EventBase):
    id: int
    status: EventStatus
    available_seats: int
    organizer_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventResponse(EventBase):
    id: int
    status: EventStatus
    available_seats: int
    organizer_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    events: List[EventResponse]
    total: int
    page: int
    page_size: int


# Search schemas
class EventSearchQuery(BaseModel):
    query: str
    category: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# Health check
class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime
