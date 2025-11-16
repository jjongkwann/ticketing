import enum

from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.sql import func

from app.db import Base


class EventStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    venue = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)

    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False)

    total_seats = Column(Integer, nullable=False)
    available_seats = Column(Integer, nullable=False)

    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)

    status = Column(SQLEnum(EventStatus), default=EventStatus.DRAFT, nullable=False, index=True)
    is_featured = Column(Boolean, default=False, nullable=False)

    organizer_id = Column(Integer, nullable=False, index=True)  # FK to users table

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 카테고리 (추후 별도 테이블로 확장 가능)
    category = Column(String(100), nullable=True, index=True)

    # 태그 (JSON 또는 별도 테이블로 관리)
    tags = Column(Text, nullable=True)

    # 이미지 URL
    image_url = Column(String(500), nullable=True)

    def __repr__(self):
        return f"<Event(id={self.id}, title={self.title}, status={self.status})>"
