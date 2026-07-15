import AsyncStorage from '@react-native-async-storage/async-storage'
import { API_BASE } from './config'

const TOKEN_KEY = 'levera_token'

function buildUrl(path: string, params?: Record<string, string>): string {
  const base = `${API_BASE}${path}`
  const q = new URLSearchParams(params || {})
  const qs = q.toString()
  return qs ? `${base}?${qs}` : base
}

async function getToken(): Promise<string | null> {
  return AsyncStorage.getItem(TOKEN_KEY)
}

export async function setToken(token: string | null): Promise<void> {
  if (token) await AsyncStorage.setItem(TOKEN_KEY, token)
  else await AsyncStorage.removeItem(TOKEN_KEY)
}

async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const token = await getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(opts.headers as Record<string, string>),
  }
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(buildUrl(path), { ...opts, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error((err as { detail?: string }).detail || res.statusText)
  }
  return res.json() as Promise<T>
}

export interface User {
  name: string
  email: string
  target_cities: string[]
  search_type: string
  profile_type: string
  equity: number
  monthly_income: number
  push_notifications?: boolean
  email_notifications?: boolean
}

export interface RegisterInput {
  name: string
  email: string
  password: string
  target_cities: string[]
}

export interface Property {
  id?: string
  city: string
  rooms?: number
  price: number
  deal_type: string
  ai_score?: number
  ai_summary?: string
  listing_url?: string
  image_url?: string
}

export interface AppNotification {
  id: string
  title: string
  message: string
  type: 'match' | 'scan' | 'weekly' | 'system'
  read: boolean
  created_at: string
}

export function login(email: string, password: string) {
  return request<{ email: string; token: string }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email: email.trim(), password, remember_me: true }),
  })
}

export function register(input: RegisterInput) {
  return request<{ email: string; token: string }>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({
      ...input,
      equity: 400_000,
      monthly_income: 12_500,
      max_repayment_ratio: 0.4,
      search_type: 'both',
      profile_type: 'HOME_BUYER',
      home_index: 1,
      loan_term_years: 30,
      room_range_min: 3,
      room_range_max: 5,
      rent_room_range_min: 2,
      rent_room_range_max: 5,
    }),
  })
}

export function getUser() {
  return request<User>('/user/me')
}

export function getProperties(params?: { view?: string; limit?: number }) {
  const q: Record<string, string> = {}
  if (params?.view) q.view = params.view
  if (params?.limit) q.limit = String(params.limit)
  const qs = new URLSearchParams(q).toString()
  return request<Property[]>(`/properties${qs ? `?${qs}` : ''}`)
}

export function getNotifications(limit = 50) {
  return request<AppNotification[]>(`/notifications?limit=${limit}`)
}

export function registerDeviceToken(token: string) {
  return request('/user/device-token', {
    method: 'POST',
    body: JSON.stringify({ token, platform: 'expo' }),
  })
}

export function updateUser(body: Partial<User>) {
  return request<User>('/user/me', { method: 'PUT', body: JSON.stringify(body) })
}

export { getToken, API_BASE }
