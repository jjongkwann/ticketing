import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from 'react-query'
import { bookingService } from '../../services/bookingService'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'

export default function MyBookingsPage() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<'upcoming' | 'past' | 'cancelled'>('upcoming')

  const { data: bookings, isLoading } = useQuery('my-bookings', bookingService.getMyBookings)

  const upcomingBookings = bookings?.filter(
    (b) => b.status === 'confirmed' && new Date(b.event?.start_date || '') > new Date()
  )
  const pastBookings = bookings?.filter(
    (b) => b.status === 'confirmed' && new Date(b.event?.start_date || '') <= new Date()
  )
  const cancelledBookings = bookings?.filter((b) => b.status === 'cancelled')

  const currentBookings = {
    upcoming: upcomingBookings || [],
    past: pastBookings || [],
    cancelled: cancelledBookings || [],
  }[activeTab]

  return (
    <div className="bg-gray-50 min-h-screen py-8">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">내 예매 내역</h1>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-sm mb-6">
          <div className="flex border-b">
            <button
              onClick={() => setActiveTab('upcoming')}
              className={`flex-1 py-4 px-6 font-medium transition-colors ${
                activeTab === 'upcoming'
                  ? 'border-b-2 border-primary-600 text-primary-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              예정된 예약 ({upcomingBookings?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('past')}
              className={`flex-1 py-4 px-6 font-medium transition-colors ${
                activeTab === 'past'
                  ? 'border-b-2 border-primary-600 text-primary-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              지난 예약 ({pastBookings?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('cancelled')}
              className={`flex-1 py-4 px-6 font-medium transition-colors ${
                activeTab === 'cancelled'
                  ? 'border-b-2 border-primary-600 text-primary-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              취소된 예약 ({cancelledBookings?.length || 0})
            </button>
          </div>
        </div>

        {/* Bookings List */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          </div>
        ) : currentBookings.length > 0 ? (
          <div className="space-y-4">
            {currentBookings.map((booking) => (
              <div
                key={booking.booking_id}
                className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => navigate(`/my/tickets/${booking.booking_id}`)}
              >
                <div className="flex items-start gap-4">
                  {/* Poster Thumbnail */}
                  <div className="w-24 h-32 bg-gray-200 rounded-lg overflow-hidden flex-shrink-0">
                    {booking.event?.poster_url ? (
                      <img
                        src={booking.event.poster_url}
                        alt={booking.event.title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-4xl">
                        🎫
                      </div>
                    )}
                  </div>

                  {/* Booking Info */}
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-gray-900 mb-2">
                      {booking.event?.title}
                    </h3>
                    <div className="space-y-1 text-sm text-gray-600 mb-3">
                      <div className="flex items-center">
                        <span className="mr-2">📅</span>
                        <span>
                          {booking.event?.start_date &&
                            format(new Date(booking.event.start_date), 'yyyy.MM.dd (eee) HH:mm', {
                              locale: ko,
                            })}
                        </span>
                      </div>
                      <div className="flex items-center">
                        <span className="mr-2">📍</span>
                        <span>{booking.event?.venue}</span>
                      </div>
                      <div className="flex items-center">
                        <span className="mr-2">🪑</span>
                        <span>{booking.seats.join(', ')}</span>
                      </div>
                      <div className="flex items-center">
                        <span className="mr-2">🎫</span>
                        <span>예약번호: {booking.booking_id}</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <span
                          className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                            booking.status === 'confirmed'
                              ? 'bg-green-100 text-green-700'
                              : booking.status === 'pending'
                              ? 'bg-yellow-100 text-yellow-700'
                              : 'bg-red-100 text-red-700'
                          }`}
                        >
                          {booking.status === 'confirmed'
                            ? '✅ 예약확정'
                            : booking.status === 'pending'
                            ? '⏰ 결제대기'
                            : '❌ 취소됨'}
                        </span>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-600">결제금액</div>
                        <div className="text-lg font-bold text-gray-900">
                          ₩{booking.total_amount.toLocaleString()}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                {activeTab === 'upcoming' && (
                  <div className="mt-4 pt-4 border-t flex gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        navigate(`/my/tickets/${booking.booking_id}`)
                      }}
                      className="btn btn-primary flex-1"
                    >
                      티켓 보기
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        if (confirm('정말 취소하시겠습니까?')) {
                          bookingService.cancelBooking(booking.booking_id)
                        }
                      }}
                      className="btn btn-outline flex-1"
                    >
                      예약 취소
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <div className="text-6xl mb-4">🎫</div>
            <p className="text-gray-500 text-lg">
              {activeTab === 'upcoming'
                ? '예정된 예약이 없습니다.'
                : activeTab === 'past'
                ? '지난 예약이 없습니다.'
                : '취소된 예약이 없습니다.'}
            </p>
            <button
              onClick={() => navigate('/')}
              className="btn btn-primary mt-4"
            >
              이벤트 둘러보기
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
