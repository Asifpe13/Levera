const API_BASE = import.meta.env.VITE_API_URL || '/api';

function getToken(): string | null {
  return localStorage.getItem('aigent_token');
}

function buildUrl(path: string, params?: Record<string, string>): string {
  const base = path.startsWith('http') ? path : API_BASE + path;
  const q = new URLSearchParams(params || {});
  const t = getToken();
  if (t && !path.startsWith('/auth')) q.set('token', t);
  const qs = q.toString();
  return qs ? base + '?' + qs : base;
}

async function request<T>(
  path: string,
  opts: RequestInit & { params?: Record<string, string> } = {}
): Promise<T> {
  const { params, ...rest } = opts;
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(rest.headers as Record<string, string>),
  };
  if (token && !path.startsWith('/auth')) headers['Authorization'] = 'Bearer ' + token;
  const res = await fetch(buildUrl(path, params), {
    ...rest,
    headers,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail || res.statusText);
  }
  return res.json();
}

export interface LoginRes {
  email: string;
  token: string | null;
}

export interface User {
  name: string;
  email: string;
  target_cities: string[];
  search_type: string;
  equity: number;
  monthly_income: number;
  room_range_min: number;
  room_range_max: number;
  max_price: number | null;
  max_repayment_ratio: number;
  rent_room_range_min: number;
  rent_room_range_max: number;
  max_rent: number | null;
  extra_preferences: string | null;
}

export function login(email: string, rememberMe: boolean): Promise<LoginRes> {
  return request<LoginRes>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email: email.trim(), remember_me: rememberMe }),
  });
}

export function register(body: {
  name: string;
  email: string;
  equity: number;
  monthly_income: number;
  max_repayment_ratio: number;
  target_cities: string[];
  search_type: string;
  room_range_min: number;
  room_range_max: number;
  max_price: number | null;
  rent_room_range_min: number;
  rent_room_range_max: number;
  max_rent: number | null;
  extra_preferences: string | null;
}): Promise<LoginRes> {
  return request<LoginRes>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function getUser(): Promise<User> {
  return request<User>('/user/me');
}

export function updateUser(updates: Partial<User>): Promise<User> {
  return request<User>('/user/me', {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
}

export function getCities(): Promise<{ cities: string[] }> {
  return fetch(buildUrl('/config/cities')).then((r) => r.json());
}

export interface Property {
  id?: string;
  source: string;
  source_id?: string;
  deal_type: 'sale' | 'rent';
  city: string;
  neighborhood?: string;
  address?: string;
  rooms?: number;
  floor?: number;
  size_sqm?: number;
  price: number;
  listing_url?: string;
  image_url?: string;
  ai_score?: number;
  ai_summary?: string;
  monthly_repayment?: number;
  price_drop?: boolean;
  value_label?: string;
  neighborhood_insights?: string;
  /** Market comparison (gov sales data): 0–100 */
  market_confidence?: number;
  /** Average ₪/sqm in area from gov data */
  market_avg_per_sqm?: number;
  /** % above/below area average */
  price_deviation_pct?: number;
  /** e.g. "Similar properties in this street were sold for ₪X per SQM (Gov data)" */
  market_summary_text?: string;
  /** סכום המשכנתא (מחיר − הון עצמי), לפי חוק המשכנתא */
  loan_amount?: number;
}

export function getProperties(params?: { deal_type?: string; city?: string; limit?: number }): Promise<Property[]> {
  const q: Record<string, string> = {};
  if (params?.deal_type) q.deal_type = params.deal_type;
  if (params?.city) q.city = params.city;
  if (params?.limit) q.limit = String(params.limit);
  return request<Property[]>('/properties/', { params: q }).then((r) => (Array.isArray(r) ? r : []));
}

export interface ScanResult {
  ok: boolean;
  log: { time: string; level: string; message: string }[];
  total_found: number;
  total_matches: number;
}

export function runScan(): Promise<ScanResult> {
  return request<ScanResult>('/scan/', { method: 'POST' });
}

export interface WeeklyReportResult {
  ok: boolean;
  message: string;
  properties_count: number;
}

export function requestWeeklyReport(): Promise<WeeklyReportResult> {
  return request<WeeklyReportResult>('/scan/weekly-report', { method: 'POST' });
}

export interface MarketTrendsByCity {
  city: string;
  avg_price: number;
  count: number;
}

export interface MarketTrends {
  total_ads: number;
  n_cities: number;
  cities: string[];
  by_city_sale: MarketTrendsByCity[];
  by_city_rent: MarketTrendsByCity[];
  total_sale: number;
  total_rent: number;
  avg_sale: number;
  avg_rent: number;
}

export function getMarketTrends(): Promise<MarketTrends> {
  return request<MarketTrends>('/market/trends');
}
