import api from '../lib/api'
import type { QueueStatus } from '../types'

export const queueService = {
  joinQueue: async (eventId: string): Promise<QueueStatus> => {
    const { data } = await api.post('/queue/join', {
      event_id: eventId,
    })
    return data
  },

  getQueueStatus: async (eventId: string): Promise<QueueStatus> => {
    const { data } = await api.get(`/queue/status/${eventId}`)
    return data
  },

  leaveQueue: async (eventId: string): Promise<void> => {
    await api.post('/queue/leave', { event_id: eventId })
  },
}
