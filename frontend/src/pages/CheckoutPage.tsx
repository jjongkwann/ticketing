import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from 'react-query'
import { loadStripe } from '@stripe/stripe-js'
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js'
import { bookingService } from '../services/bookingService'
import { paymentService } from '../services/paymentService'
import { useAuthStore } from '../store/authStore'

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLIC_KEY || '')

function CheckoutForm({ bookingId }: { bookingId: string }) {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const stripe = useStripe()
  const elements = useElements()
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { data: booking } = useQuery(['booking', bookingId], () =>
    bookingService.getBookingById(bookingId)
  )

  const [payerInfo, setPayerInfo] = useState({
    name: user?.name || '',
    phone: user?.phone || '',
    email: user?.email || '',
  })

  // Timer
  const [timeLeft, setTimeLeft] = useState(600) // 10 minutes

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 0) {
          alert('예약 시간이 만료되었습니다.')
          navigate('/')
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [navigate])

  const minutes = Math.floor(timeLeft / 60)
  const seconds = timeLeft % 60

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!stripe || !elements || !booking) {
      return
    }

    setIsProcessing(true)
    setError(null)

    try {
      // Create payment intent
      const { client_secret } = await paymentService.createPaymentIntent(bookingId)

      // Confirm card payment
      const cardElement = elements.getElement(CardElement)
      if (!cardElement) {
        throw new Error('Card element not found')
      }

      const { error: stripeError, paymentIntent } = await stripe.confirmCardPayment(
        client_secret,
        {
          payment_method: {
            card: cardElement,
            billing_details: {
              name: payerInfo.name,
              email: payerInfo.email,
              phone: payerInfo.phone,
            },
          },
        }
      )

      if (stripeError) {
        throw new Error(stripeError.message)
      }

      if (paymentIntent?.status === 'succeeded') {
        // Confirm booking
        await bookingService.confirmBooking(bookingId)
        navigate(`/checkout/complete/${bookingId}`)
      }
    } catch (err: any) {
      setError(err.message || '결제에 실패했습니다.')
    } finally {
      setIsProcessing(false)
    }
  }

  if (!booking) {
    return <div>Loading...</div>
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Timer */}
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <span className="text-red-700 font-medium">예약 만료까지</span>
            <span
              className={`text-2xl font-bold ${
                timeLeft < 60 ? 'text-red-600' : 'text-red-700'
              }`}
            >
              ⏰ {minutes.toString().padStart(2, '0')}:{seconds.toString().padStart(2, '0')}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left: Booking Summary */}
          <div>
            <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
              <h2 className="text-xl font-bold mb-4">예약 정보</h2>
              <div className="space-y-3">
                <div>
                  <div className="text-sm text-gray-600">이벤트</div>
                  <div className="font-medium">{booking.event?.title}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">날짜</div>
                  <div className="font-medium">{booking.event?.start_date}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">좌석</div>
                  <div className="font-medium">{booking.seats.join(', ')}</div>
                </div>
                <div className="border-t pt-3">
                  <div className="flex justify-between text-lg font-bold">
                    <span>총 결제 금액</span>
                    <span className="text-primary-600">
                      ₩{booking.total_amount.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right: Payment Form */}
          <div>
            <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-bold mb-6">결제 정보</h2>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
                  {error}
                </div>
              )}

              {/* Payer Info */}
              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    예매자 이름
                  </label>
                  <input
                    type="text"
                    className="input"
                    value={payerInfo.name}
                    onChange={(e) => setPayerInfo({ ...payerInfo, name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    전화번호
                  </label>
                  <input
                    type="tel"
                    className="input"
                    value={payerInfo.phone}
                    onChange={(e) => setPayerInfo({ ...payerInfo, phone: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    이메일
                  </label>
                  <input
                    type="email"
                    className="input"
                    value={payerInfo.email}
                    onChange={(e) => setPayerInfo({ ...payerInfo, email: e.target.value })}
                    required
                  />
                </div>
              </div>

              {/* Card Element */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  카드 정보
                </label>
                <div className="border border-gray-300 rounded-lg p-3">
                  <CardElement
                    options={{
                      style: {
                        base: {
                          fontSize: '16px',
                          color: '#424770',
                          '::placeholder': {
                            color: '#aab7c4',
                          },
                        },
                        invalid: {
                          color: '#9e2146',
                        },
                      },
                    }}
                  />
                </div>
              </div>

              {/* Terms */}
              <div className="mb-6">
                <label className="flex items-start">
                  <input type="checkbox" className="mt-1 mr-2" required />
                  <span className="text-sm text-gray-700">
                    개인정보 수집 및 이용, 예매 취소 및 환불 규정에 동의합니다
                  </span>
                </label>
              </div>

              <button
                type="submit"
                disabled={!stripe || isProcessing}
                className="w-full btn btn-primary text-lg py-3 disabled:opacity-50"
              >
                {isProcessing
                  ? '결제 처리 중...'
                  : `₩${booking.total_amount.toLocaleString()} 결제하기`}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function CheckoutPage() {
  const { bookingId } = useParams<{ bookingId: string }>()

  return (
    <Elements stripe={stripePromise}>
      <CheckoutForm bookingId={bookingId!} />
    </Elements>
  )
}
