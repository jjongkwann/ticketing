import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from 'react-query'
import { eventService } from '../services/eventService'
import EventCard from '../components/EventCard'
import type { SearchFilters } from '../types'

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [filters, setFilters] = useState<SearchFilters>({
    q: searchParams.get('q') || '',
    category: searchParams.get('category') || '',
    sort: 'relevance',
  })

  const { data: events, isLoading } = useQuery(
    ['search-events', filters],
    () => eventService.searchEvents(filters),
    {
      enabled: !!filters.q || !!filters.category,
    }
  )

  useEffect(() => {
    const params: any = {}
    if (filters.q) params.q = filters.q
    if (filters.category) params.category = filters.category
    if (filters.sort) params.sort = filters.sort
    setSearchParams(params)
  }, [filters])

  const categories = [
    { id: '', name: '전체' },
    { id: 'concert', name: '콘서트' },
    { id: 'sports', name: '스포츠' },
    { id: 'musical', name: '뮤지컬' },
    { id: 'exhibition', name: '전시회' },
  ]

  const sortOptions = [
    { value: 'relevance', label: '관련성순' },
    { value: 'date', label: '날짜순' },
    { value: 'price_low', label: '가격 낮은순' },
    { value: 'price_high', label: '가격 높은순' },
  ]

  return (
    <div className="bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <div className="flex flex-col md:flex-row gap-4">
            <input
              type="text"
              placeholder="아티스트, 공연, 장소 검색..."
              className="input flex-1"
              value={filters.q}
              onChange={(e) => setFilters({ ...filters, q: e.target.value })}
            />
            <select
              className="input md:w-48"
              value={filters.sort}
              onChange={(e) => setFilters({ ...filters, sort: e.target.value as any })}
            >
              {sortOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Category Filters */}
          <div className="flex gap-2 mt-4 overflow-x-auto">
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setFilters({ ...filters, category: cat.id })}
                className={`px-4 py-2 rounded-full whitespace-nowrap transition-all ${
                  filters.category === cat.id
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {cat.name}
              </button>
            ))}
          </div>
        </div>

        {/* Results */}
        <div>
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-900">
              검색 결과
              {events && <span className="text-primary-600 ml-2">({events.length}건)</span>}
            </h2>
          </div>

          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="card h-96 animate-pulse bg-gray-200"></div>
              ))}
            </div>
          ) : events && events.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {events.map((event) => (
                <EventCard key={event.event_id} event={event} />
              ))}
            </div>
          ) : (
            <div className="text-center py-20">
              <p className="text-gray-500 text-lg">검색 결과가 없습니다.</p>
              <p className="text-gray-400 mt-2">다른 검색어로 시도해보세요.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
