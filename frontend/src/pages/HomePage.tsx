import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from 'react-query'
import { eventService } from '../services/eventService'
import EventCard from '../components/EventCard'

export default function HomePage() {
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')

  const { data: eventsData, isLoading } = useQuery('featured-events', () =>
    eventService.getEvents({ sort: 'date' })
  )

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`)
    }
  }

  const categories = [
    { id: 'concert', name: '콘서트', icon: '🎤' },
    { id: 'sports', name: '스포츠', icon: '⚽' },
    { id: 'musical', name: '뮤지컬', icon: '🎭' },
    { id: 'exhibition', name: '전시회', icon: '🎨' },
  ]

  return (
    <div className="bg-gray-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-primary-600 to-purple-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center">
            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              🎉 원하는 공연을 찾아보세요
            </h1>
            <p className="text-xl mb-8 opacity-90">
              대한민국 No.1 티켓팅 플랫폼, Ticketing Pro
            </p>

            {/* Search Bar */}
            <form onSubmit={handleSearch} className="max-w-2xl mx-auto">
              <div className="relative">
                <input
                  type="text"
                  placeholder="아티스트, 공연, 장소 검색..."
                  className="w-full px-6 py-4 rounded-full text-gray-900 text-lg focus:outline-none focus:ring-4 focus:ring-white/30"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <button
                  type="submit"
                  className="absolute right-2 top-1/2 -translate-y-1/2 bg-primary-600 text-white px-8 py-2 rounded-full hover:bg-primary-700"
                >
                  검색
                </button>
              </div>
            </form>

            {/* Category Buttons */}
            <div className="flex justify-center gap-4 mt-8">
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => navigate(`/search?category=${cat.id}`)}
                  className="bg-white/20 hover:bg-white/30 px-6 py-3 rounded-full backdrop-blur-sm transition-all"
                >
                  <span className="mr-2">{cat.icon}</span>
                  {cat.name}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Featured Events */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900">🔥 지금 가장 HOT한 공연</h2>
          <button
            onClick={() => navigate('/search')}
            className="text-primary-600 hover:text-primary-700 font-medium"
          >
            더보기 →
          </button>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="card h-96 animate-pulse bg-gray-200"></div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {eventsData?.data.slice(0, 8).map((event) => (
              <EventCard key={event.event_id} event={event} />
            ))}
          </div>
        )}
      </div>

      {/* Category Sections */}
      {categories.map((category) => (
        <div key={category.id} className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">
              {category.icon} {category.name}
            </h2>
            <button
              onClick={() => navigate(`/search?category=${category.id}`)}
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              더보기 →
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {eventsData?.data.slice(0, 3).map((event) => (
              <EventCard key={event.event_id} event={event} />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
