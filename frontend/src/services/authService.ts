import api from '../lib/api'
import type { LoginRequest, RegisterRequest, AuthResponse, User } from '../types'

export const authService = {
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    const { data } = await api.post('/auth/login', credentials)
    return data
  },

  register: async (userData: RegisterRequest): Promise<AuthResponse> => {
    const { data } = await api.post('/auth/register', userData)
    return data
  },

  getMe: async (): Promise<User> => {
    const { data } = await api.get('/auth/me')
    return data
  },

  logout: async (): Promise<void> => {
    // Optional: call backend logout endpoint if needed
    // await api.post('/auth/logout')
  },
}
