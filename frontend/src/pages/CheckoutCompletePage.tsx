import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from 'react-query'
import { bookingService } from '../services/bookingService'
import { QRCodeSVG } from 'qrcode.react'

export default function CheckoutCompletePage() {
  const { bookingId } = useParams<{ bookingId: string }>()
  const navigate = useNavigate()

  const { data: booking, isLoading } = useQuery(['booking', bookingId], () =>
    bookingService.getBookingById(bookingId!)
  )

  if (isLoading || !booking) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Success Header */}
        <div className="text-center mb-8">
          <div className="text-6xl mb-4">✅</div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">예매가 완료되었습니다!</h1>
          <p className="text-gray-600">
            예약번호: <span className="font-medium">{booking.booking_id}</span>
          </p>
        </div>

        {/* Booking Info Card */}
        <div className="bg-white rounded-lg shadow-sm p-8 mb-6">
          {/* QR Code */}
          <div className="flex justify-center mb-6">
            <div className="bg-gray-100 p-4 rounded-lg">
              <QRCodeSVG value={booking.booking_id} size={200} />
              <p className="text-center text-xs text-gray-500 mt-2">입장 시 제시</p>
            </div>
          </div>

          {/* Divider */}
          <div className="border-t my-6"></div>

          {/* Event Details */}
          <div className="space-y-4">
            <div>
              <div className="text-sm text-gray-600 mb-1">이벤트</div>
              <div className="text-lg font-bold">{booking.event?.title}</div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-600 mb-1">날짜</div>
                <div className="font-medium">
                  {booking.event?.start_date}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600 mb-1">장소</div>
                <div className="font-medium">{booking.event?.venue}</div>
              </div>
            </div>

            <div>
              <div className="text-sm text-gray-600 mb-1">좌석</div>
              <div className="font-medium">{booking.seats.join(', ')}</div>
            </div>

            <div className="border-t pt-4">
              <div className="flex justify-between items-center">
                <span className="text-lg font-bold">결제 금액</span>
                <span className="text-2xl font-bold text-primary-600">
                  ₩{booking.total_amount.toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Email Notice */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <span className="text-2xl">📧</span>
            <div className="text-sm text-gray-700">
              <p className="font-semibold mb-1">예약 확인 이메일이 발송되었습니다</p>
              <p>등록하신 이메일 주소로 예약 정보와 티켓이 발송되었습니다.</p>
            </div>
          </div>
        </div>

        {/* Refund Policy */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h3 className="font-bold mb-3">취소 및 환불 안내</h3>
          <ul className="space-y-2 text-sm text-gray-700">
            <li>• 공연일 7일 전까지: 전액 환불</li>
            <li>• 공연일 3일 전까지: 80% 환불</li>
            <li>• 공연일 1일 전까지: 50% 환불</li>
            <li>• 공연 당일: 환불 불가</li>
          </ul>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button
            onClick={() => navigate(`/my/tickets/${booking.booking_id}`)}
            className="flex-1 btn btn-primary"
          >
            티켓 확인하기
          </button>
          <button
            onClick={() => navigate('/my/bookings')}
            className="flex-1 btn btn-outline"
          >
            내 예약 보기
          </button>
        </div>
      </div>
    </div>
  )
}
