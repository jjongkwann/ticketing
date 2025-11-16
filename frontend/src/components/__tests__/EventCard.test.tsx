import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import EventCard from '../EventCard'
import type { Event } from '../../types'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

const mockEvent: Event = {
  event_id: 'evt_123',
  title: 'BTS World Tour 2024',
  description: 'Amazing concert',
  category: 'concert',
  venue: '잠실 올림픽 주경기장',
  address: '서울시 송파구',
  start_date: '2024-05-20T18:00:00',
  end_date: '2024-05-20T21:00:00',
  poster_url: 'https://example.com/poster.jpg',
  status: 'published',
  min_price: 150000,
  max_price: 300000,
  available_seats: 500,
  total_seats: 5000,
  created_at: '2024-01-01T00:00:00',
}

describe('EventCard', () => {
  const renderEventCard = () => {
    return render(
      <BrowserRouter>
        <EventCard event={mockEvent} />
      </BrowserRouter>
    )
  }

  it('renders event information correctly', () => {
    renderEventCard()

    expect(screen.getByText('BTS World Tour 2024')).toBeInTheDocument()
    expect(screen.getByText('잠실 올림픽 주경기장')).toBeInTheDocument()
    expect(screen.getByText(/₩150,000 ~/)).toBeInTheDocument()
  })

  it('displays available seats count', () => {
    renderEventCard()

    expect(screen.getByText(/500석 남음/)).toBeInTheDocument()
  })

  it('shows "매진 임박" when less than 10% seats available', () => {
    const almostSoldOut = {
      ...mockEvent,
      available_seats: 400, // 400/5000 = 8% < 10%
    }

    render(
      <BrowserRouter>
        <EventCard event={almostSoldOut} />
      </BrowserRouter>
    )

    expect(screen.getByText(/매진 임박/)).toBeInTheDocument()
  })

  it('navigates to event detail page on click', () => {
    renderEventCard()

    const card = screen.getByText('BTS World Tour 2024').closest('.card')
    fireEvent.click(card!)

    expect(mockNavigate).toHaveBeenCalledWith('/events/evt_123')
  })

  it('renders poster image when available', () => {
    renderEventCard()

    const img = screen.getByAltText('BTS World Tour 2024')
    expect(img).toHaveAttribute('src', mockEvent.poster_url)
  })

  it('shows placeholder when no poster image', () => {
    const noPosterEvent = { ...mockEvent, poster_url: '' }

    render(
      <BrowserRouter>
        <EventCard event={noPosterEvent} />
      </BrowserRouter>
    )

    expect(screen.getByText('🎫')).toBeInTheDocument()
  })
})
