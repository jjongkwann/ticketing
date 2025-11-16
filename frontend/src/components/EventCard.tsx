import { useNavigate } from 'react-router-dom'
import type { Event } from '../types'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'

interface EventCardProps {
  event: Event
}

export default function EventCard({ event }: EventCardProps) {
  const navigate = useNavigate()

  const formattedDate = format(new Date(event.start_date), 'yyyy.MM.dd (eee) HH:mm', {
    locale: ko,
  })

  const remainingSeats = event.available_seats
  const isAlmostSoldOut = remainingSeats < event.total_seats * 0.1

  return (
    <div
      onClick={() => navigate(`/events/${event.event_id}`)}
      className="card cursor-pointer overflow-hidden group"
    >
      {/* Poster Image */}
      <div className="aspect-[3/4] overflow-hidden bg-gray-200">
        {event.poster_url ? (
          <img
            src={event.poster_url}
            alt={event.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <span className="text-6xl">🎫</span>
          </div>
        )}
      </div>

      {/* Event Info */}
      <div className="p-4">
        <h3 className="font-bold text-lg text-gray-900 mb-2 line-clamp-1">{event.title}</h3>

        <div className="space-y-1 text-sm text-gray-600 mb-3">
          <div className="flex items-center">
            <span className="mr-2">📅</span>
            <span>{formattedDate}</span>
          </div>
          <div className="flex items-center">
            <span className="mr-2">📍</span>
            <span className="line-clamp-1">{event.venue}</span>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="text-lg font-bold text-primary-600">
            ₩{event.min_price.toLocaleString()} ~
          </div>
          {isAlmostSoldOut ? (
            <span className="text-xs text-red-600 font-semibold">🔥 매진 임박</span>
          ) : (
            <span className="text-xs text-gray-500">
              🎫 {remainingSeats.toLocaleString()}석 남음
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
