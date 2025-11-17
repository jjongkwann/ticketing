import api from '../lib/api'
import type { Event, EventDetail, SearchFilters, PaginatedResponse } from '../types'

export const eventService = {
  getEvents: async (filters?: SearchFilters): Promise<PaginatedResponse<Event>> => {
    const { data } = await api.get('/events', { params: filters })
    // API returns {events: [], ...} but we need {data: [], ...}
    return {
      data: data.events || [],
      total: data.total || 0,
      page: data.page || 1,
      per_page: data.page_size || 20,
      total_pages: Math.ceil((data.total || 0) / (data.page_size || 20)),
    }
  },

  getEventById: async (eventId: string): Promise<EventDetail> => {
    const { data } = await api.get(`/events/${eventId}`)
    return data
  },

  searchEvents: async (filters: SearchFilters): Promise<Event[]> => {
    const { data } = await api.get('/search/events', { params: filters })
    return data.events || []
  },

  createEvent: async (eventData: Partial<Event>): Promise<Event> => {
    const { data } = await api.post('/events', eventData)
    return data
  },
}
