import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from 'react-query'
import { bookingService } from '../../services/bookingService'
import { QRCodeSVG } from 'qrcode.react'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'

export default function TicketDetailPage() {
  const { bookingId } = useParams<{ bookingId: string }>()
  const [qrToken, setQrToken] = useState(Date.now().toString())
  const [secondsLeft, setSecondsLeft] = useState(60)

  const { data: booking, isLoading } = useQuery(['booking', bookingId], () =>
    bookingService.getBookingById(bookingId!)
  )

  // Rotate QR code every 60 seconds (SafeTix feature)
  useEffect(() => {
    const interval = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          setQrToken(Date.now().toString())
          return 60
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  if (isLoading || !booking) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  // Generate rotating QR data (SafeTix)
  const qrData = `${booking.booking_id}:${qrToken}`

  return (
    <div className="bg-gray-50 min-h-screen py-8">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* SafeTix Header */}
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">SafeTix</h1>
          <p className="text-sm text-gray-600">
            위조 방지를 위한 동적 QR 코드 티켓
          </p>
        </div>

        {/* Ticket Card */}
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden mb-6">
          {/* Rotating QR Code */}
          <div className="bg-gradient-to-br from-primary-600 to-purple-600 p-8">
            <div className="bg-white rounded-2xl p-6">
              <div className="flex justify-center mb-4">
                <QRCodeSVG
                  value={qrData}
                  size={250}
                  level="H"
                  includeMargin={true}
                />
              </div>

              {/* Rotation Indicator */}
              <div className="text-center">
                <div className="inline-block bg-gray-100 rounded-full px-4 py-2">
                  <div className="flex items-center gap-2 text-sm">
                    <div className={`w-2 h-2 rounded-full ${
                      secondsLeft <= 10 ? 'bg-red-500 animate-pulse' : 'bg-green-500'
                    }`}></div>
                    <span className="font-medium">
                      {secondsLeft}초 후 자동 갱신
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-4 text-center text-xs text-gray-500">
                🔒 이 QR 코드는 60초마다 변경되어 위조를 방지합니다
              </div>
            </div>
          </div>

          {/* Event Info */}
          <div className="p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              {booking.event?.title}
            </h2>

            <div className="space-y-3 text-gray-700">
              <div className="flex items-center">
                <span className="w-6 mr-3">📅</span>
                <span>
                  {booking.event?.start_date &&
                    format(new Date(booking.event.start_date), 'yyyy.MM.dd (eee) HH:mm', {
                      locale: ko,
                    })}
                </span>
              </div>
              <div className="flex items-center">
                <span className="w-6 mr-3">📍</span>
                <span>{booking.event?.venue}</span>
              </div>
              <div className="flex items-center">
                <span className="w-6 mr-3">🪑</span>
                <span>{booking.seats.join(', ')}</span>
              </div>
              <div className="flex items-center">
                <span className="w-6 mr-3">🎫</span>
                <span className="font-mono text-sm">{booking.booking_id}</span>
              </div>
            </div>

            <div className="mt-6 pt-6 border-t">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">결제 금액</span>
                <span className="text-2xl font-bold text-gray-900">
                  ₩{booking.total_amount.toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Notice */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <h3 className="font-bold text-yellow-900 mb-2">입장 안내</h3>
          <ul className="space-y-1 text-sm text-yellow-800">
            <li>• 입장 시 이 화면의 QR 코드를 제시해주세요</li>
            <li>• QR 코드는 60초마다 자동으로 변경됩니다</li>
            <li>• 스크린샷은 무효이니 실시간 화면을 보여주세요</li>
            <li>• 공연 시작 30분 전부터 입장 가능합니다</li>
          </ul>
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-4">
          <button className="btn btn-outline">
            📱 Apple Wallet 추가
          </button>
          <button className="btn btn-outline">
            📧 이메일로 전송
          </button>
        </div>

        {/* Additional Info */}
        <div className="mt-6 bg-white rounded-lg p-4">
          <h3 className="font-bold mb-3">주의사항</h3>
          <ul className="space-y-2 text-sm text-gray-700">
            <li>• 티켓은 타인에게 양도할 수 없습니다</li>
            <li>• 공연장 내 촬영 및 녹음이 금지됩니다</li>
            <li>• 음식물 반입이 불가합니다</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
