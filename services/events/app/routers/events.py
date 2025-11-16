from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from datetime import datetime

from app.db import get_db
from app.models import Event, EventStatus
from app.schemas import (
    EventCreate,
    EventResponse,
    EventUpdate,
    EventListResponse,
    EventSearchQuery,
)
from app.search import index_event, update_event_in_index, delete_event_from_index, search_events

router = APIRouter(prefix="/events", tags=["events"])


# 임시: 인증 시뮬레이션 (실제로는 Auth Service와 통합)
async def get_current_user_id() -> int:
    """임시 사용자 ID (실제로는 JWT 토큰에서 추출)"""
    return 1  # 임시 하드코딩


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """이벤트 생성"""
    # 시간 검증
    if event_data.end_time <= event_data.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time",
        )

    # 새 이벤트 생성
    new_event = Event(
        title=event_data.title,
        description=event_data.description,
        venue=event_data.venue,
        address=event_data.address,
        start_time=event_data.start_time,
        end_time=event_data.end_time,
        total_seats=event_data.total_seats,
        available_seats=event_data.total_seats,  # 초기에는 전체 좌석이 사용 가능
        price=event_data.price,
        currency=event_data.currency,
        category=event_data.category,
        tags=event_data.tags,
        image_url=event_data.image_url,
        is_featured=event_data.is_featured,
        organizer_id=user_id,
        status=EventStatus.DRAFT,  # 초기 상태는 Draft
    )

    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)

    # OpenSearch 인덱싱 (비동기)
    event_dict = {
        "id": new_event.id,
        "title": new_event.title,
        "description": new_event.description,
        "venue": new_event.venue,
        "address": new_event.address,
        "start_time": new_event.start_time,
        "end_time": new_event.end_time,
        "total_seats": new_event.total_seats,
        "available_seats": new_event.available_seats,
        "price": new_event.price,
        "currency": new_event.currency,
        "status": new_event.status.value,
        "category": new_event.category,
        "tags": new_event.tags,
        "is_featured": new_event.is_featured,
        "organizer_id": new_event.organizer_id,
        "created_at": new_event.created_at,
    }
    await index_event(event_dict)

    return new_event


@router.get("", response_model=EventListResponse)
async def list_events(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    status: Optional[EventStatus] = None,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """이벤트 목록 조회"""
    query = select(Event)

    # 필터 적용
    filters = []
    if status:
        filters.append(Event.status == status)
    if category:
        filters.append(Event.category == category)

    if filters:
        query = query.where(and_(*filters))

    # 정렬: featured 우선, 시작 시간 순
    query = query.order_by(Event.is_featured.desc(), Event.start_time.asc())

    # 전체 개수
    count_query = select(func.count()).select_from(Event)
    if filters:
        count_query = count_query.where(and_(*filters))
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 페이지네이션
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    events = result.scalars().all()

    return EventListResponse(
        events=events,
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
    )


@router.get("/search", response_model=EventListResponse)
async def search_events_endpoint(
    query: str = Query(..., min_length=1),
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """이벤트 검색 (OpenSearch)"""
    result = await search_events(
        query=query,
        category=category,
        min_price=min_price,
        max_price=max_price,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )

    return EventListResponse(
        events=result["events"],
        total=result["total"],
        page=page,
        page_size=page_size,
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    """이벤트 상세 조회"""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return event


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_update: EventUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """이벤트 수정"""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    # 권한 확인 (이벤트 생성자만 수정 가능)
    if event.organizer_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # 수정
    update_data = event_update.model_dump(exclude_unset=True)

    # 시간 검증
    start_time = update_data.get("start_time", event.start_time)
    end_time = update_data.get("end_time", event.end_time)
    if end_time <= start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time",
        )

    for key, value in update_data.items():
        setattr(event, key, value)

    await db.commit()
    await db.refresh(event)

    # OpenSearch 업데이트
    event_dict = {k: getattr(event, k) for k in update_data.keys()}
    if "status" in event_dict:
        event_dict["status"] = event_dict["status"].value
    await update_event_in_index(event_id, event_dict)

    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """이벤트 삭제"""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    # 권한 확인
    if event.organizer_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    await db.delete(event)
    await db.commit()

    # OpenSearch에서 삭제
    await delete_event_from_index(event_id)


@router.post("/{event_id}/publish", response_model=EventResponse)
async def publish_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """이벤트 게시"""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    if event.organizer_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    event.status = EventStatus.PUBLISHED
    await db.commit()
    await db.refresh(event)

    # OpenSearch 업데이트
    await update_event_in_index(event_id, {"status": "published"})

    return event
