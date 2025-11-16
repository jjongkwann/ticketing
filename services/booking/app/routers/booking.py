import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.dynamodb import get_dynamodb_repo
from app.grpc_client import get_inventory_client
from app.kafka_producer import get_kafka_producer
from app.schemas import BookingConfirm, BookingCreate, BookingListResponse, BookingResponse

router = APIRouter(prefix="/bookings", tags=["bookings"])


# 임시: 인증 시뮬레이션
async def get_current_user_id() -> str:
    """임시 사용자 ID"""
    return "user-123"


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(booking_data: BookingCreate, user_id: str = Depends(get_current_user_id)):
    """예약 생성 (좌석 예약)"""
    inventory_client = get_inventory_client()
    dynamodb_repo = get_dynamodb_repo()
    kafka_producer = get_kafka_producer()

    # Step 1: Inventory Service에 좌석 예약 요청 (gRPC)
    try:
        reserve_result = await inventory_client.reserve_seat(
            event_id=booking_data.event_id, seat_number=booking_data.seat_number, user_id=user_id
        )

        if not reserve_result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=reserve_result.get("message", "Failed to reserve seat")
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Inventory service error: {str(e)}"
        )

    # Step 2: DynamoDB에 예약 기록 저장
    booking_id = str(uuid.uuid4())
    reservation_id = reserve_result.get("reservation_id")

    booking = {
        "booking_id": booking_id,
        "event_id": booking_data.event_id,
        "seat_number": booking_data.seat_number,
        "user_id": user_id,
        "status": "pending",
        "reservation_id": reservation_id,
        "price": 100.0,  # TODO: Get from event
        "created_at": datetime.utcnow(),
    }

    try:
        await dynamodb_repo.create_booking(booking)
    except Exception as e:
        # Rollback: release seat
        await inventory_client.release_seat(booking_data.event_id, booking_data.seat_number, user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create booking: {str(e)}"
        )

    # Step 3: Kafka 이벤트 발행
    try:
        await kafka_producer.publish_booking_created(booking)
    except Exception as e:
        # Log but don't fail the request
        print(f"Warning: Failed to publish Kafka event: {e}")

    return BookingResponse(**booking)


@router.post("/{booking_id}/confirm", response_model=BookingResponse)
async def confirm_booking(booking_id: str, confirm_data: BookingConfirm, user_id: str = Depends(get_current_user_id)):
    """예약 확정 (결제 완료 후)"""
    inventory_client = get_inventory_client()
    dynamodb_repo = get_dynamodb_repo()
    kafka_producer = get_kafka_producer()

    # Step 1: 예약 조회
    booking = await dynamodb_repo.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    # 권한 확인
    if booking["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    # 상태 확인
    if booking["status"] != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Booking already {booking['status']}")

    # Step 2: Inventory Service에 확정 요청
    try:
        confirm_result = await inventory_client.confirm_booking(
            reservation_id=booking["reservation_id"], user_id=user_id, payment_id=confirm_data.payment_id
        )

        if not confirm_result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=confirm_result.get("message", "Failed to confirm booking"),
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Inventory service error: {str(e)}"
        )

    # Step 3: DynamoDB 업데이트
    try:
        updated_booking = await dynamodb_repo.update_booking_status(booking_id, "confirmed", confirm_data.payment_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update booking: {str(e)}"
        )

    # Step 4: Kafka 이벤트 발행
    try:
        await kafka_producer.publish_booking_confirmed(updated_booking)
    except Exception as e:
        print(f"Warning: Failed to publish Kafka event: {e}")

    return BookingResponse(**updated_booking)


@router.get("/my", response_model=BookingListResponse)
async def list_my_bookings(user_id: str = Depends(get_current_user_id)):
    """내 예약 목록"""
    dynamodb_repo = get_dynamodb_repo()

    try:
        bookings = await dynamodb_repo.list_user_bookings(user_id)
        return BookingListResponse(bookings=[BookingResponse(**b) for b in bookings], total=len(bookings))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list bookings: {str(e)}"
        )


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: str, user_id: str = Depends(get_current_user_id)):
    """예약 상세 조회"""
    dynamodb_repo = get_dynamodb_repo()

    booking = await dynamodb_repo.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    return BookingResponse(**booking)


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_booking(booking_id: str, user_id: str = Depends(get_current_user_id)):
    """예약 취소"""
    dynamodb_repo = get_dynamodb_repo()
    inventory_client = get_inventory_client()

    booking = await dynamodb_repo.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    # 확정된 예약은 취소 불가
    if booking["status"] == "confirmed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel confirmed booking")

    # Inventory Service에 좌석 해제 요청
    try:
        await inventory_client.release_seat(booking["event_id"], booking["seat_number"], user_id)
    except Exception as e:
        print(f"Warning: Failed to release seat: {e}")

    # DynamoDB 업데이트
    await dynamodb_repo.update_booking_status(booking_id, "cancelled")
