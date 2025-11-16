import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from 'react-query'
import { queueService } from '../services/queueService'
import { eventService } from '../services/eventService'

export default function QueuePage() {
  const { eventId } = useParams<{ eventId: string }>()
  const navigate = useNavigate()
  const [queueToken, setQueueToken] = useState<string | null>(null)

  // Join queue on mount
  useEffect(() => {
    const joinQueue = async () => {
      try {
        const status = await queueService.joinQueue(eventId!)
        if (status.queue_token) {
          setQueueToken(status.queue_token)
        }
      } catch (error) {
        console.error('Failed to join queue:', error)
      }
    }

    joinQueue()

    return () => {
      // Leave queue on unmount
      queueService.leaveQueue(eventId!)
    }
  }, [eventId])

  // Poll queue status
  const { data: queueStatus } = useQuery(
    ['queue-status', eventId],
    () => queueService.getQueueStatus(eventId!),
    {
      refetchInterval: 5000, // Poll every 5 seconds
      enabled: !!queueToken,
    }
  )

  const { data: event } = useQuery(['event', eventId], () =>
    eventService.getEventById(eventId!)
  )

  // Redirect when can proceed
  useEffect(() => {
    if (queueStatus?.can_proceed) {
      navigate(`/events/${eventId}`)
    }
  }, [queueStatus, eventId, navigate])

  if (!event || !queueStatus) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  const progress = queueStatus.total_in_queue > 0
    ? ((queueStatus.total_in_queue - queueStatus.queue_position) / queueStatus.total_in_queue) * 100
    : 0

  const estimatedMinutes = Math.ceil(queueStatus.estimated_wait_time / 60)

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-600 to-purple-600 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-2xl shadow-2xl p-8 md:p-12">
        {/* Event Info */}
        <div className="text-center mb-8">
          <div className="text-5xl mb-4">🎫</div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
            {event.title}
          </h1>
          <p className="text-gray-600">티켓 오픈 대기 중</p>
        </div>

        {/* Queue Position */}
        <div className="text-center mb-8">
          <div className="text-sm text-gray-600 mb-2">현재 대기 인원</div>
          <div className="text-5xl font-bold text-primary-600 mb-4">
            {queueStatus.total_in_queue.toLocaleString()}명
          </div>

          <div className="text-sm text-gray-600 mb-2">내 순번</div>
          <div className="text-4xl font-bold text-gray-900">
            #{queueStatus.queue_position.toLocaleString()}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="w-full bg-gray-200 rounded-full h-6 overflow-hidden">
            <div
              className="bg-gradient-to-r from-primary-600 to-purple-600 h-full transition-all duration-500 rounded-full flex items-center justify-center text-white text-sm font-bold"
              style={{ width: `${progress}%` }}
            >
              {progress > 10 && `${Math.round(progress)}%`}
            </div>
          </div>
          <p className="text-center text-sm text-gray-600 mt-2">
            {progress < 100 ? `${Math.round(progress)}% 완료` : '거의 다 왔어요!'}
          </p>
        </div>

        {/* Estimated Wait Time */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-600 mb-1">예상 대기 시간</div>
              <div className="text-3xl font-bold text-blue-600">
                약 {estimatedMinutes}분
              </div>
            </div>
            <div className="text-5xl">⏰</div>
          </div>
        </div>

        {/* Warning */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <span className="text-2xl">⚠️</span>
            <div className="text-sm text-gray-700">
              <p className="font-semibold mb-1">이 창을 닫지 마세요</p>
              <p>순번이 되면 자동으로 티켓 선택 페이지로 이동됩니다.</p>
              <p className="mt-2 text-xs text-gray-600">
                새로고침 시 대기열 맨 뒤로 이동될 수 있습니다.
              </p>
            </div>
          </div>
        </div>

        {/* Live Indicator */}
        <div className="mt-8 flex items-center justify-center gap-2 text-gray-500 text-sm">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span>실시간 업데이트 중...</span>
        </div>
      </div>
    </div>
  )
}
