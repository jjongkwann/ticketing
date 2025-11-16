import api from '../lib/api'
import type { Event, EventDetail, SearchFilters, PaginatedResponse } from '../types'

export const eventService = {
  getEvents: async (filters?: SearchFilters): Promise<PaginatedResponse<Event>> => {
    const { data } = await api.get('/events', { params: filters })
    return data
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
