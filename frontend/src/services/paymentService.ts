import api from '../lib/api'

export interface PaymentIntentResponse {
  payment_intent_id: string
  client_secret: string
  amount: number
}

export const paymentService = {
  createPaymentIntent: async (bookingId: string): Promise<PaymentIntentResponse> => {
    const { data } = await api.post('/payments/create-intent', {
      booking_id: bookingId,
    })
    return data
  },
}
