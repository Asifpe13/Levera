import AsyncStorage from '@react-native-async-storage/async-storage'
import { API_BASE } from './config'

const TOKEN_KEY = 'levera_token'
const FETCH_TIMEOUT_MS = 60_000

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

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS)

  try {
    const res = await fetch(buildUrl(path), { ...opts, headers, signal: controller.signal })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error((err as { detail?: string }).detail || res.statusText)
    }
    return res.json() as Promise<T>
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new Error('הבקשה לקחה יותר מדי זמן — נסה שוב')
    }
    throw err
  } finally {
    clearTimeout(timer)
  }
}

export interface User {
  name: string
  email: string
  target_cities: string[]
  search_type: 'buy' | 'rent' | 'both'
  profile_type: 'HOME_BUYER' | 'INVESTOR' | 'CASH_FLOW_MAXIMIZER'
  home_index: number
  loan_term_years: number
  equity: number
  monthly_income: number
  room_range_min: number
  room_range_max: number
  max_price: number | null
  max_repayment_ratio: number
  rent_room_range_min: number
  rent_room_range_max: number
  max_rent: number | null
  extra_preferences: string | null
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
  source: string
  city: string
  neighborhood?: string
  address?: string
  rooms?: number
  floor?: number
  size_sqm?: number
  price: number
  deal_type: 'sale' | 'rent'
  ai_score?: number
  ai_summary?: string
  listing_url?: string
  image_url?: string
  monthly_repayment?: number
  loan_amount?: number
  market_confidence?: number
  market_avg_per_sqm?: number
  price_deviation_pct?: number
  market_summary_text?: string
  profile_area_message?: string
  value_label?: string
  price_drop?: boolean
  neighborhood_insights?: string
}

export interface AppNotification {
  id: string
  title: string
  message: string
  type: 'match' | 'scan' | 'weekly' | 'system'
  read: boolean
  created_at: string
}

export interface ScanRejections {
  high_mortgage?: number
  over_budget?: number
  wrong_rooms?: number
  suspicious?: number
  irrelevant?: number
  low_score?: number
  other?: number
}

export interface ScanStatus {
  running: boolean
  finished: boolean
  message: string
  total_found: number
  total_matches: number
  log: { time: string; level: string; message: string }[]
  rejections: ScanRejections
  progress?: number
}

export interface WeeklyReportResult {
  ok: boolean
  message: string
  properties_count: number
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

export function getProperties(params?: {
  view?: 'latest' | 'all'
  limit?: number
  deal_type?: 'sale' | 'rent'
  city?: string
}) {
  const q: Record<string, string> = {}
  if (params?.view) q.view = params.view
  if (params?.limit) q.limit = String(params.limit)
  if (params?.deal_type) q.deal_type = params.deal_type
  if (params?.city) q.city = params.city
  const qs = new URLSearchParams(q).toString()
  return request<Property[]>(`/properties${qs ? `?${qs}` : ''}`)
}

export function startScan() {
  return request<{ status: 'started' | 'already_running' }>('/scan', { method: 'POST' })
}

export async function getScanStatus(): Promise<ScanStatus> {
  const token = await getToken()
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 8_000)
  try {
    const res = await fetch(buildUrl('/scan/status'), {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      signal: controller.signal,
    })
    if (!res.ok) throw new Error(res.statusText)
    return res.json() as Promise<ScanStatus>
  } finally {
    clearTimeout(timer)
  }
}

export function requestWeeklyReport() {
  return request<WeeklyReportResult>('/scan/weekly-report', { method: 'POST' })
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
