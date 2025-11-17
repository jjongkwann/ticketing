import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from 'react-query'
import { eventService } from '../services/eventService'
import { bookingService } from '../services/bookingService'
import { useCartStore } from '../store/cartStore'
import { useAuthStore } from '../store/authStore'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import SeatSelection from '../components/SeatSelection'

export default function EventDetailPage() {
  const { eventId } = useParams<{ eventId: string }>()
  const navigate = useNavigate()
  const { isAuthenticated } = useAuthStore()
  const { selectedSeats, clearCart } = useCartStore()
  const [activeTab, setActiveTab] = useState<'info' | 'seats' | 'reviews'>('info')
  const [isBooking, setIsBooking] = useState(false)

  const { data: event, isLoading } = useQuery(['event', eventId], () =>
    eventService.getEventById(eventId!)
  )

  const handleBooking = async () => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }

    if (selectedSeats.length === 0) {
      alert('좌석을 선택해주세요.')
      return
    }

    setIsBooking(true)
    try {
      const booking = await bookingService.createBooking(eventId!, selectedSeats)
      clearCart()
      navigate(`/checkout/${booking.booking_id}`)
    } catch (error: any) {
      alert(error.response?.data?.message || '예약에 실패했습니다.')
    } finally {
      setIsBooking(false)
    }
  }

  if (isLoading || !event) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  const formattedDate = format(new Date(event.start_date), 'yyyy.MM.dd (eee) HH:mm', {
    locale: ko,
  })

  const totalPrice = selectedSeats.reduce((sum) => {
    // Simple calculation - in real app, get seat price from seat data
    return sum + event.min_price
  }, 0)

  return (
    <div className="bg-gray-50">
      {/* Hero Section */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Poster */}
            <div className="md:col-span-1">
              <div className="aspect-[3/4] bg-gray-200 rounded-xl overflow-hidden">
                {event.poster_url ? (
                  <img
                    src={event.poster_url}
                    alt={event.title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <span className="text-8xl">🎫</span>
                  </div>
                )}
              </div>
            </div>

            {/* Event Info */}
            <div className="md:col-span-2">
              <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                {event.title}
              </h1>

              <div className="space-y-3 text-gray-700 mb-6">
                <div className="flex items-center text-lg">
                  <span className="mr-3">📅</span>
                  <span>{formattedDate}</span>
                </div>
                <div className="flex items-center text-lg">
                  <span className="mr-3">📍</span>
                  <span>{event.venue}</span>
                </div>
                <div className="flex items-center text-lg">
                  <span className="mr-3">⏱️</span>
                  <span>약 150분 (인터미션 포함)</span>
                </div>
                <div className="flex items-center text-lg">
                  <span className="mr-3">👤</span>
                  <span>관람등급: 만 7세 이상</span>
                </div>
              </div>

              <div className="bg-primary-50 rounded-lg p-4 mb-6">
                <div className="text-sm text-gray-600 mb-1">가격</div>
                <div className="text-2xl font-bold text-primary-600">
                  ₩{event.min_price.toLocaleString()} ~ ₩{event.max_price.toLocaleString()}
                </div>
              </div>

              <div className="flex gap-4">
                <button className="btn btn-outline flex-1">
                  🔗 공유하기
                </button>
                <button className="btn btn-outline flex-1">
                  ♡ 찜하기
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b sticky top-16 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-8">
            <button
              onClick={() => setActiveTab('info')}
              className={`py-4 px-2 border-b-2 font-medium transition-colors ${
                activeTab === 'info'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              📄 상세정보
            </button>
            <button
              onClick={() => setActiveTab('seats')}
              className={`py-4 px-2 border-b-2 font-medium transition-colors ${
                activeTab === 'seats'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              🪑 좌석선택
            </button>
            <button
              onClick={() => setActiveTab('reviews')}
              className={`py-4 px-2 border-b-2 font-medium transition-colors ${
                activeTab === 'reviews'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              ⭐ 관람후기
            </button>
          </div>
        </div>
      </div>

      {/* Tab Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'info' && (
          <div className="bg-white rounded-lg p-8">
            <h2 className="text-2xl font-bold mb-4">공연 소개</h2>
            <p className="text-gray-700 whitespace-pre-wrap mb-8">{event.description}</p>

            <h3 className="text-xl font-bold mb-4">유의사항</h3>
            <ul className="list-disc list-inside text-gray-700 space-y-2">
              <li>만 7세 이상 관람가</li>
              <li>공연 시작 후 입장 불가</li>
              <li>티켓 예매 후 취소는 공연 7일 전까지 가능</li>
            </ul>
          </div>
        )}

        {activeTab === 'seats' && (
          <div className="bg-white rounded-lg p-8">
            <SeatSelection event={event} />
          </div>
        )}

        {activeTab === 'reviews' && (
          <div className="bg-white rounded-lg p-8">
            <p className="text-gray-500 text-center py-8">아직 등록된 후기가 없습니다.</p>
          </div>
        )}
      </div>

      {/* Fixed Bottom Bar */}
      {activeTab === 'seats' && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600">
                  선택한 좌석: {selectedSeats.length}석
                </div>
                <div className="text-2xl font-bold text-primary-600">
                  총 ₩{totalPrice.toLocaleString()}
                </div>
              </div>
              <button
                onClick={handleBooking}
                disabled={selectedSeats.length === 0 || isBooking}
                className="btn btn-primary text-lg px-12 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isBooking ? '예매 중...' : '예매하기 →'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
