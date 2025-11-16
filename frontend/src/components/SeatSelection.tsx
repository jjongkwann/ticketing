import { useState, useEffect } from 'react'
import { useCartStore } from '../store/cartStore'
import type { EventDetail, Seat } from '../types'

interface SeatSelectionProps {
  event: EventDetail
}

export default function SeatSelection({ event }: SeatSelectionProps) {
  const { selectedSeats, addSeat, removeSeat, setEvent } = useCartStore()
  const [seats, setSeats] = useState<Seat[]>([])

  useEffect(() => {
    setEvent(event.event_id)

    // Generate mock seats for demo
    const mockSeats: Seat[] = []
    event.sections.forEach((section) => {
      for (let row = 0; row < 10; row++) {
        for (let col = 0; col < 10; col++) {
          const seatNumber = `${String.fromCharCode(65 + row)}${col + 1}`
          mockSeats.push({
            seat_id: `${section.section_id}-${seatNumber}`,
            section_id: section.section_id,
            seat_number: seatNumber,
            row: String.fromCharCode(65 + row),
            status: Math.random() > 0.7 ? 'sold' : 'available',
            price: section.price,
            position: { x: col * 40, y: row * 40 },
          })
        }
      }
    })
    setSeats(mockSeats)
  }, [event])

  const handleSeatClick = (seat: Seat) => {
    if (seat.status === 'sold') return

    if (selectedSeats.includes(seat.seat_id)) {
      removeSeat(seat.seat_id)
    } else {
      if (selectedSeats.length >= 4) {
        alert('최대 4석까지 선택 가능합니다.')
        return
      }
      addSeat(seat.seat_id)
    }
  }

  const getSeatColor = (seat: Seat) => {
    if (selectedSeats.includes(seat.seat_id)) return 'bg-blue-500 hover:bg-blue-600'
    if (seat.status === 'sold') return 'bg-red-500 cursor-not-allowed'
    if (seat.status === 'reserved') return 'bg-yellow-500 cursor-not-allowed'
    return 'bg-green-500 hover:bg-green-600 cursor-pointer'
  }

  return (
    <div>
      <div className="mb-6">
        <h3 className="text-xl font-bold mb-4">좌석 범례</h3>
        <div className="flex gap-6">
          <div className="flex items-center">
            <div className="w-6 h-6 bg-green-500 rounded mr-2"></div>
            <span className="text-sm">🟢 예약 가능</span>
          </div>
          <div className="flex items-center">
            <div className="w-6 h-6 bg-yellow-500 rounded mr-2"></div>
            <span className="text-sm">🟡 임시 예약</span>
          </div>
          <div className="flex items-center">
            <div className="w-6 h-6 bg-red-500 rounded mr-2"></div>
            <span className="text-sm">🔴 예약 완료</span>
          </div>
          <div className="flex items-center">
            <div className="w-6 h-6 bg-blue-500 rounded mr-2"></div>
            <span className="text-sm">🔵 선택중</span>
          </div>
        </div>
      </div>

      {/* Sections */}
      {event.sections.map((section) => (
        <div key={section.section_id} className="mb-8">
          <h4 className="text-lg font-bold mb-4">
            {section.name} (₩{section.price.toLocaleString()})
          </h4>

          <div className="bg-gray-100 p-6 rounded-lg overflow-x-auto">
            {/* Stage */}
            <div className="text-center mb-6">
              <div className="inline-block bg-gray-800 text-white px-12 py-3 rounded-lg">
                STAGE
              </div>
            </div>

            {/* Seats Grid */}
            <div className="grid grid-cols-10 gap-2 max-w-2xl mx-auto">
              {seats
                .filter((s) => s.section_id === section.section_id)
                .map((seat) => (
                  <button
                    key={seat.seat_id}
                    onClick={() => handleSeatClick(seat)}
                    className={`w-10 h-10 rounded text-xs text-white font-medium transition-all ${getSeatColor(
                      seat
                    )}`}
                    title={`${seat.seat_number} - ${seat.status}`}
                  >
                    {seat.seat_number}
                  </button>
                ))}
            </div>
          </div>

          <div className="mt-4 text-sm text-gray-600">
            잔여 좌석: {section.available_seats}/{section.total_seats}석
          </div>
        </div>
      ))}

      {/* Selected Seats Summary */}
      {selectedSeats.length > 0 && (
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h4 className="font-bold text-lg mb-3">선택한 좌석</h4>
          <div className="flex flex-wrap gap-2">
            {selectedSeats.map((seatId) => {
              const seat = seats.find((s) => s.seat_id === seatId)
              return (
                <div
                  key={seatId}
                  className="bg-white px-4 py-2 rounded-full border border-blue-300 flex items-center gap-2"
                >
                  <span>{seat?.seat_number}</span>
                  <button
                    onClick={() => removeSeat(seatId)}
                    className="text-red-600 hover:text-red-700"
                  >
                    ✕
                  </button>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
