export default function AdminEventNew() {
  return (
    <div className="bg-gray-50 min-h-screen py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">새 이벤트 등록</h1>

        <form className="bg-white rounded-lg shadow-sm p-8">
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                이벤트명 *
              </label>
              <input type="text" className="input" placeholder="BTS World Tour 2024" />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  카테고리 *
                </label>
                <select className="input">
                  <option>콘서트</option>
                  <option>스포츠</option>
                  <option>뮤지컬</option>
                  <option>전시회</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  장소 *
                </label>
                <input type="text" className="input" placeholder="잠실 올림픽 주경기장" />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  시작 일시 *
                </label>
                <input type="datetime-local" className="input" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  종료 일시
                </label>
                <input type="datetime-local" className="input" />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                상세 설명
              </label>
              <textarea className="input" rows={6} placeholder="이벤트 상세 설명..."></textarea>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                포스터 이미지
              </label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                <p className="text-gray-600">클릭하거나 드래그하여 이미지 업로드</p>
              </div>
            </div>

            <div className="pt-6 border-t">
              <h3 className="text-lg font-bold mb-4">좌석 및 가격 설정</h3>
              <div className="space-y-3">
                <div className="grid grid-cols-3 gap-4">
                  <input type="text" className="input" placeholder="VIP석" />
                  <input type="number" className="input" placeholder="가격 (원)" />
                  <input type="number" className="input" placeholder="좌석 수" />
                </div>
                <button type="button" className="btn btn-outline w-full">
                  + 구역 추가
                </button>
              </div>
            </div>

            <div className="flex gap-4 pt-6">
              <button type="button" className="flex-1 btn btn-outline">
                취소
              </button>
              <button type="submit" className="flex-1 btn btn-primary">
                이벤트 등록
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}
