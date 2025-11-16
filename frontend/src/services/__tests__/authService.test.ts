import { describe, it, expect, vi, beforeEach } from 'vitest'
import { authService } from '../authService'
import api from '../../lib/api'

vi.mock('../../lib/api')

describe('authService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('login', () => {
    it('should login successfully with valid credentials', async () => {
      const mockResponse = {
        data: {
          access_token: 'mock_token',
          refresh_token: 'mock_refresh',
          user: {
            user_id: 'usr_123',
            email: 'test@example.com',
            name: 'Test User',
            phone: '010-1234-5678',
            created_at: '2024-01-01T00:00:00',
          },
        },
      }

      vi.mocked(api.post).mockResolvedValue(mockResponse)

      const result = await authService.login({
        email: 'test@example.com',
        password: 'password123',
      })

      expect(api.post).toHaveBeenCalledWith('/auth/login', {
        email: 'test@example.com',
        password: 'password123',
      })

      expect(result).toEqual(mockResponse.data)
      expect(result.user.email).toBe('test@example.com')
    })

    it('should throw error on invalid credentials', async () => {
      const mockError = {
        response: {
          data: {
            message: 'Invalid credentials',
          },
        },
      }

      vi.mocked(api.post).mockRejectedValue(mockError)

      await expect(
        authService.login({
          email: 'wrong@example.com',
          password: 'wrongpassword',
        })
      ).rejects.toThrow()
    })
  })

  describe('register', () => {
    it('should register new user successfully', async () => {
      const mockResponse = {
        data: {
          access_token: 'mock_token',
          refresh_token: 'mock_refresh',
          user: {
            user_id: 'usr_456',
            email: 'newuser@example.com',
            name: 'New User',
            phone: '010-9876-5432',
            created_at: '2024-01-15T00:00:00',
          },
        },
      }

      vi.mocked(api.post).mockResolvedValue(mockResponse)

      const result = await authService.register({
        email: 'newuser@example.com',
        password: 'password123',
        name: 'New User',
        phone: '010-9876-5432',
      })

      expect(api.post).toHaveBeenCalledWith('/auth/register', {
        email: 'newuser@example.com',
        password: 'password123',
        name: 'New User',
        phone: '010-9876-5432',
      })

      expect(result.user.email).toBe('newuser@example.com')
    })
  })

  describe('getMe', () => {
    it('should fetch current user data', async () => {
      const mockUser = {
        data: {
          user_id: 'usr_123',
          email: 'test@example.com',
          name: 'Test User',
          phone: '010-1234-5678',
          created_at: '2024-01-01T00:00:00',
        },
      }

      vi.mocked(api.get).mockResolvedValue(mockUser)

      const result = await authService.getMe()

      expect(api.get).toHaveBeenCalledWith('/auth/me')
      expect(result.email).toBe('test@example.com')
    })
  })
})
