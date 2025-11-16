import api from '../lib/api'
import type { Booking, BookingDetail } from '../types'

export const bookingService = {
  createBooking: async (eventId: string, seats: string[]): Promise<Booking> => {
    const { data } = await api.post('/bookings', {
      event_id: eventId,
      seats,
    })
    return data
  },

  getMyBookings: async (): Promise<Booking[]> => {
    const { data } = await api.get('/bookings/my')
    return data.bookings || []
  },

  getBookingById: async (bookingId: string): Promise<BookingDetail> => {
    const { data } = await api.get(`/bookings/${bookingId}`)
    return data
  },

  confirmBooking: async (bookingId: string): Promise<BookingDetail> => {
    const { data } = await api.post(`/bookings/${bookingId}/confirm`)
    return data
  },

  cancelBooking: async (bookingId: string): Promise<void> => {
    await api.post(`/bookings/${bookingId}/cancel`)
  },
}
