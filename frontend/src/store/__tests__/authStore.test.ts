import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from '../authStore'
import type { User } from '../../types'

describe('authStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
    })
  })

  it('should initialize with unauthenticated state', () => {
    const state = useAuthStore.getState()

    expect(state.user).toBeNull()
    expect(state.token).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })

  it('should set authentication state', () => {
    const mockUser: User = {
      user_id: 'usr_123',
      email: 'test@example.com',
      name: 'Test User',
      phone: '010-1234-5678',
      created_at: '2024-01-01T00:00:00',
    }

    const mockToken = 'mock_jwt_token'

    useAuthStore.getState().setAuth(mockUser, mockToken)

    const state = useAuthStore.getState()

    expect(state.user).toEqual(mockUser)
    expect(state.token).toBe(mockToken)
    expect(state.isAuthenticated).toBe(true)
  })

  it('should logout and clear state', () => {
    const mockUser: User = {
      user_id: 'usr_123',
      email: 'test@example.com',
      name: 'Test User',
      phone: '010-1234-5678',
      created_at: '2024-01-01T00:00:00',
    }

    // First login
    useAuthStore.getState().setAuth(mockUser, 'mock_token')

    // Then logout
    useAuthStore.getState().logout()

    const state = useAuthStore.getState()

    expect(state.user).toBeNull()
    expect(state.token).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })
})
