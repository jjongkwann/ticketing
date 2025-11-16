# Ticketing Pro - Frontend

Ticketmaster 수준의 엔터프라이즈 티켓팅 플랫폼 프론트엔드

## 기술 스택

- **React 18** + TypeScript
- **Vite** - 빌드 도구
- **Tailwind CSS** - 스타일링
- **React Router** - 라우팅
- **React Query** - 서버 상태 관리
- **Zustand** - 클라이언트 상태 관리
- **Stripe** - 결제 통합
- **Socket.io** - 실시간 통신 (좌석 상태)

## 주요 기능

### 🎫 핵심 기능
- 이벤트 검색 및 필터링
- 실시간 좌석 선택
- Stripe 결제 통합
- 예약 관리

### 🚀 Ticketmaster Pro 기능
- **Virtual Waiting Room** - 대기열 시스템
- **SafeTix** - 60초 갱신 동적 QR 코드
- **Verified Fan** - 팬 인증 배지
- **Dynamic Pricing** - 수요 기반 가격 책정 (준비 중)

## 설치 및 실행

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 프로덕션 빌드
npm run build

# 프리뷰
npm run preview
```

## 환경 변수

`.env.example`을 `.env`로 복사하고 값을 설정하세요:

```env
VITE_API_URL=http://localhost:8000/api
VITE_STRIPE_PUBLIC_KEY=your_stripe_public_key
```

## 프로젝트 구조

```
src/
├── components/       # 재사용 가능한 컴포넌트
│   ├── layout/      # Header, Footer 등
│   ├── EventCard.tsx
│   └── SeatSelection.tsx
├── pages/           # 페이지 컴포넌트
│   ├── auth/        # 로그인, 회원가입
│   ├── my/          # 마이페이지
│   ├── admin/       # 관리자
│   └── ...
├── services/        # API 서비스
├── store/           # Zustand 상태 관리
├── types/           # TypeScript 타입
└── lib/             # 유틸리티
```

## API 연동

백엔드 API는 `/api` 경로로 프록시됩니다 (개발 환경):

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

## 주요 페이지

- `/` - 메인 페이지
- `/search` - 검색 결과
- `/events/:id` - 이벤트 상세
- `/queue/:id` - 대기열 (Virtual Waiting Room)
- `/checkout/:id` - 결제
- `/my/bookings` - 내 예약
- `/my/tickets/:id` - 티켓 (SafeTix)

## 배포

```bash
# 빌드
npm run build

# dist 폴더를 서버에 배포
```

## 라이센스

MIT
