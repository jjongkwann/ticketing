// Event Types
export interface Event {
  event_id: string
  title: string
  description: string
  category: string
  venue: string
  address: string
  start_date: string
  end_date: string
  poster_url: string
  status: 'published' | 'draft' | 'cancelled'
  min_price: number
  max_price: number
  available_seats: number
  total_seats: number
  created_at: string
}

export interface EventDetail extends Event {
  sections: Section[]
  reviews?: Review[]
}

export interface Section {
  section_id: string
  name: string
  price: number
  total_seats: number
  available_seats: number
}

export interface Seat {
  seat_id: string
  section_id: string
  seat_number: string
  row: string
  status: 'available' | 'reserved' | 'sold' | 'selected'
  price: number
  position?: { x: number; y: number }
}

export interface Review {
  review_id: string
  user_name: string
  rating: number
  comment: string
  created_at: string
}

// Booking Types
export interface Booking {
  booking_id: string
  event_id: string
  user_id: string
  seats: string[]
  total_amount: number
  status: 'pending' | 'confirmed' | 'cancelled'
  expires_at: string
  created_at: string
  event?: Event
}

export interface BookingDetail extends Booking {
  event: EventDetail
  payment?: Payment
  qr_code?: string
}

// Payment Types
export interface Payment {
  payment_id: string
  booking_id: string
  amount: number
  payment_method: string
  status: 'pending' | 'succeeded' | 'failed'
  stripe_payment_intent_id?: string
  created_at: string
}

// Auth Types
export interface User {
  user_id: string
  email: string
  name: string
  phone: string
  verified_fan_tier?: 'platinum' | 'gold' | 'silver' | 'bronze'
  created_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  name: string
  phone: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  user: User
}

// Queue Types
export interface QueueStatus {
  queue_position: number
  total_in_queue: number
  estimated_wait_time: number // seconds
  queue_token?: string
  can_proceed: boolean
}

// Search Types
export interface SearchFilters {
  q?: string
  category?: string
  min_price?: number
  max_price?: number
  start_date?: string
  end_date?: string
  location?: string
  sort?: 'relevance' | 'date' | 'price_low' | 'price_high'
}

// SafeTix Types
export interface SafeTixData {
  ticket_id: string
  booking_id: string
  qr_code_data: string
  qr_code_image: string
  expires_at: string
  rotation_interval: number
}

// API Response Types
export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface ApiError {
  error: string
  message: string
  status_code: number
}

// Pagination
export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}
