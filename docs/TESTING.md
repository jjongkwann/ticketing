# Testing Documentation

## Overview

This document describes the comprehensive testing infrastructure for the Ticketing Pro application, including unit tests, integration tests, E2E tests, and CI/CD pipeline.

## Table of Contents

1. [Frontend Testing](#frontend-testing)
2. [Backend Testing](#backend-testing)
3. [E2E Testing](#e2e-testing)
4. [CI/CD Pipeline](#cicd-pipeline)
5. [Running Tests](#running-tests)
6. [Coverage Reports](#coverage-reports)

---

## Frontend Testing

### Tech Stack

- **Vitest**: Fast unit test framework with native ESM support
- **React Testing Library**: Component testing utilities
- **jsdom**: Browser environment simulation
- **@vitest/coverage-v8**: Code coverage reporting

### Test Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── __tests__/
│   │       └── EventCard.test.tsx
│   ├── services/
│   │   └── __tests__/
│   │       └── authService.test.ts
│   ├── store/
│   │   └── __tests__/
│   │       └── authStore.test.ts
│   └── test/
│       └── setup.ts
└── vitest.config.ts
```

### What's Tested

#### Component Tests
- **EventCard** (`components/__tests__/EventCard.test.tsx`)
  - Renders event information correctly
  - Navigates to event detail on click
  - Displays seat availability
  - Shows proper pricing format

#### Service Tests
- **authService** (`services/__tests__/authService.test.ts`)
  - Login with valid credentials
  - Register new user
  - Get current user info
  - Handle API errors

#### Store Tests
- **authStore** (`store/__tests__/authStore.test.ts`)
  - Set authentication state
  - Logout clears state
  - Persist to localStorage

### Running Frontend Tests

```bash
# Run all tests
cd frontend
npm run test

# Run with UI
npm run test:ui

# Generate coverage report
npm run test:coverage
```

### Coverage Goals

- **Statements**: > 80%
- **Branches**: > 75%
- **Functions**: > 80%
- **Lines**: > 80%

---

## Backend Testing

### Tech Stack

- **pytest**: Python testing framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **httpx**: HTTP client for testing FastAPI
- **moto**: AWS service mocking
- **unittest.mock**: Mock library

### Test Structure

```
services/
├── api-gateway/
│   └── tests/
│       ├── __init__.py
│       └── test_main.py
├── auth/
│   └── tests/
│       ├── __init__.py
│       └── test_auth.py
├── events/
│   └── tests/
│       ├── __init__.py
│       └── test_events.py
├── booking/
│   └── tests/
│       ├── __init__.py
│       └── test_booking.py
└── payment/
    └── tests/
        ├── __init__.py
        └── test_payment.py
```

### What's Tested

#### API Gateway Tests (`api-gateway/tests/test_main.py`)
- Health check endpoint
- Rate limiting (10 requests/minute)
- Proxy to auth service
- Proxy to events service
- CORS headers
- Invalid service routes

#### Auth Service Tests (`auth/tests/test_auth.py`)
- User registration
  - Success case
  - Duplicate email handling
- User login
  - Valid credentials
  - Invalid password
  - Non-existent user
- Get current user
  - Authenticated
  - Unauthenticated
  - Invalid token

#### Events Service Tests (`events/tests/test_events.py`)
- Create event
- Get events list
- Filter by category
- Get event by ID
- Update event
- Publish event
- Cancel event
- Get event seats
- Pagination

#### Payment Service Tests (`payment/tests/test_payment.py`)
- Create payment intent
  - Valid amount
  - Invalid amount
- Get payment status
- Cancel payment
- Webhook handling
  - Payment succeeded
  - Payment failed
- Refund payment
- Multiple payment intents

#### Booking Service Tests (`booking/tests/test_booking.py`)
- Create booking
  - Standard booking (1-4 seats)
  - Maximum seats (4)
  - Exceeds maximum (>4 - should fail)
- Get booking by ID
- Get user bookings
- Confirm booking
- Cancel booking
- Booking expiration (10 minutes)
- Concurrent booking prevention
- Invalid seat handling
- Unauthorized access

### Running Backend Tests

```bash
# API Gateway
cd services/api-gateway
pytest --cov=app --cov-report=html

# Auth Service
cd services/auth
pytest --cov=app --cov-report=html

# Events Service
cd services/events
pytest --cov=app --cov-report=html

# Payment Service
cd services/payment
pytest --cov=app --cov-report=html

# Booking Service
cd services/booking
pytest --cov=app --cov-report=html
```

### Coverage Goals

- **Statements**: > 80%
- **Branches**: > 75%
- **Functions**: > 80%

---

## E2E Testing

### Tech Stack

- **Playwright**: Modern E2E testing framework
- **Multi-browser support**: Chromium, Firefox, WebKit
- **Mobile testing**: Pixel 5, iPhone 12

### Test Structure

```
frontend/
├── e2e/
│   ├── auth.spec.ts
│   └── event-search.spec.ts
└── playwright.config.ts
```

### What's Tested

#### Authentication Flow (`e2e/auth.spec.ts`)
1. Display login page
   - Shows logo "Ticketing Pro"
   - Email and password fields visible
2. Validation errors on empty submit
3. Navigate to register page
4. Display register form
5. Validate password strength

#### Event Search Flow (`e2e/event-search.spec.ts`)
1. Display main page with search bar
2. Navigate to search page on submit
3. Display category filters (콘서트, 스포츠, 뮤지컬, 전시회)
4. Filter by category
5. Display search results
6. Show event cards

### Running E2E Tests

```bash
cd frontend

# Install browsers (first time only)
npx playwright install --with-deps

# Run tests
npm run test:e2e

# Run with UI
npm run test:e2e:ui

# Run specific browser
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit

# Run mobile tests
npx playwright test --project="Mobile Chrome"
npx playwright test --project="Mobile Safari"
```

### Configuration

- **Base URL**: `http://localhost:3000`
- **Retries**: 2 (in CI), 0 (local)
- **Workers**: 1 (in CI), unlimited (local)
- **Screenshots**: Only on failure
- **Trace**: On first retry

---

## CI/CD Pipeline

### GitHub Actions Workflow

Location: `.github/workflows/ci.yml`

### Jobs

#### 1. Frontend Test
- Setup Node.js 18
- Install dependencies
- Run linter
- Run TypeScript type check
- Run unit tests
- Generate coverage report
- Upload to Codecov

#### 2. Frontend E2E
- Setup Node.js 18
- Install dependencies
- Install Playwright browsers
- Run E2E tests
- Upload Playwright report

#### 3. Backend Tests
Parallel jobs for each service:
- **API Gateway**: Python 3.11, pytest
- **Auth Service**: Python 3.11, pytest, PostgreSQL
- **Events Service**: Python 3.11, pytest, PostgreSQL
- **Payment Service**: Python 3.11, pytest, Stripe mocks
- **Inventory Service**: Go 1.21, go test

Each backend job:
- Installs dependencies
- Runs tests with coverage
- Uploads coverage to Codecov

#### 4. Build Frontend
- Only on push to `main`
- Builds production bundle
- Uploads build artifacts

#### 5. Docker Build
- Only on push to `main`
- Builds and pushes Docker images for all services
- Tags: `latest` and `{commit-sha}`
- Uses GitHub Actions cache

### Triggers

- **Push**: `main`, `develop` branches
- **Pull Request**: `main`, `develop` branches

### Secrets Required

- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub password
- `CODECOV_TOKEN`: Codecov upload token (optional)

---

## Running Tests

### Quick Start

```bash
# Frontend tests
cd frontend
npm run test              # Unit + Integration
npm run test:e2e         # E2E tests
npm run test:coverage    # Coverage report

# Backend tests
cd services/auth
pytest --cov=app         # Auth service tests

cd ../events
pytest --cov=app         # Events service tests

cd ../payment
pytest --cov=app         # Payment service tests

cd ../booking
pytest --cov=app         # Booking service tests

cd ../api-gateway
pytest --cov=app         # API Gateway tests

# Go tests (Inventory service)
cd services/inventory
go test -v -race -coverprofile=coverage.out ./...
```

### Full Test Suite

```bash
# Run all tests (requires all services to be set up)
./scripts/run-all-tests.sh
```

---

## Coverage Reports

### Viewing Coverage

#### Frontend
```bash
cd frontend
npm run test:coverage
# Open coverage/index.html in browser
```

#### Backend
```bash
cd services/auth
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

### Coverage on Codecov

After pushing to GitHub, coverage reports are automatically uploaded to Codecov:

- Frontend: `flags: frontend`
- API Gateway: `flags: api-gateway`
- Auth Service: `flags: auth-service`
- Events Service: `flags: events-service`
- Payment Service: `flags: payment-service`
- Booking Service: `flags: booking-service`
- Inventory Service: `flags: inventory-service`

---

## Test Best Practices

### Frontend

1. **Use Testing Library queries**: Prefer `getByRole`, `getByText` over `querySelector`
2. **Test user behavior**: Simulate actual user interactions
3. **Avoid implementation details**: Don't test internal state
4. **Mock API calls**: Use MSW or vi.mock for API responses

### Backend

1. **Use test databases**: SQLite for speed, PostgreSQL replica for integration
2. **Clean up after tests**: Use fixtures with `autouse=True`
3. **Mock external services**: Stripe, AWS, gRPC services
4. **Test edge cases**: Validation errors, rate limits, concurrent access

### E2E

1. **Use data-testid sparingly**: Prefer semantic selectors
2. **Wait for elements**: Use `expect().toBeVisible()` instead of hardcoded delays
3. **Test critical paths**: Focus on user journeys, not every button
4. **Keep tests independent**: Each test should set up its own data

---

## Troubleshooting

### Frontend Tests Failing

```bash
# Clear cache
rm -rf node_modules/.vite
npm run test

# Update snapshots
npm run test -- -u
```

### Backend Tests Failing

```bash
# Recreate test database
rm -f test.db test_events.db

# Clear pytest cache
rm -rf .pytest_cache

# Run with verbose output
pytest -vv
```

### E2E Tests Failing

```bash
# Update browsers
npx playwright install --with-deps

# Run with headed mode
npx playwright test --headed

# Debug specific test
npx playwright test --debug event-search.spec.ts
```

---

## Next Steps

1. **Expand test coverage**: Add more edge cases and scenarios
2. **Performance testing**: Use Locust or k6 for load testing
3. **Security testing**: Add OWASP ZAP or similar tools
4. **Contract testing**: Add Pact for microservices contracts
5. **Visual regression**: Add Percy or similar for UI testing

---

## Summary

✅ **Frontend Testing**: Vitest + React Testing Library
✅ **Backend Testing**: pytest with comprehensive service tests
✅ **E2E Testing**: Playwright with multi-browser support
✅ **CI/CD Pipeline**: GitHub Actions with automated testing
✅ **Coverage Reporting**: Codecov integration

**Total Test Files**: 13+
**Test Coverage Goal**: > 80%
**CI/CD Status**: Fully automated
