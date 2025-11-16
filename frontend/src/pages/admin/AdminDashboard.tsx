export default function AdminDashboard() {
  const stats = [
    { label: '총 판매', value: '₩12,450,000', change: '+12%' },
    { label: '예약 건수', value: '245', change: '+8%' },
    { label: '활성 이벤트', value: '12', change: '+3%' },
    { label: '방문자', value: '5,432', change: '+15%' },
  ]

  return (
    <div className="bg-gray-50 min-h-screen py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">관리자 대시보드</h1>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => (
            <div key={index} className="bg-white rounded-lg shadow-sm p-6">
              <div className="text-sm text-gray-600 mb-1">{stat.label}</div>
              <div className="text-3xl font-bold text-gray-900 mb-2">{stat.value}</div>
              <div className="text-sm text-green-600">{stat.change}</div>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold mb-4">빠른 작업</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button className="btn btn-primary">새 이벤트 등록</button>
            <button className="btn btn-outline">예약 관리</button>
            <button className="btn btn-outline">통계 보기</button>
          </div>
        </div>
      </div>
    </div>
  )
}
