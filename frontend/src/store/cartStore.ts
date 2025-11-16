import { create } from 'zustand'

interface CartState {
  selectedSeats: string[]
  eventId: string | null
  addSeat: (seatId: string) => void
  removeSeat: (seatId: string) => void
  clearCart: () => void
  setEvent: (eventId: string) => void
}

export const useCartStore = create<CartState>((set) => ({
  selectedSeats: [],
  eventId: null,

  addSeat: (seatId) =>
    set((state) => ({
      selectedSeats: [...state.selectedSeats, seatId],
    })),

  removeSeat: (seatId) =>
    set((state) => ({
      selectedSeats: state.selectedSeats.filter((id) => id !== seatId),
    })),

  clearCart: () =>
    set({
      selectedSeats: [],
      eventId: null,
    }),

  setEvent: (eventId) =>
    set({
      eventId,
      selectedSeats: [],
    }),
}))
