export default function Footer() {
  return (
    <footer className="bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <h3 className="text-lg font-bold mb-4">Ticketing Pro</h3>
            <p className="text-gray-400 text-sm">
              엔터프라이즈급 티켓팅 플랫폼
            </p>
          </div>

          <div>
            <h4 className="font-semibold mb-4">고객센터</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>
                <a href="#" className="hover:text-white">
                  자주 묻는 질문
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white">
                  1:1 문의
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white">
                  환불 안내
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-4">회사 정보</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>
                <a href="#" className="hover:text-white">
                  회사 소개
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white">
                  이용약관
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white">
                  개인정보처리방침
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-4">고객센터</h4>
            <p className="text-2xl font-bold mb-2">1588-0000</p>
            <p className="text-sm text-gray-400">평일 09:00 - 18:00</p>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-8 text-sm text-gray-400 text-center">
          <p>Copyright © 2024 Ticketing Pro. All rights reserved.</p>
        </div>
      </div>
    </footer>
  )
}
