const API_BASE = import.meta.env.VITE_API_URL || '/api';
const FETCH_TIMEOUT_MS = 60_000;

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

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);

  try {
    const res = await fetch(buildUrl(path, params), {
      ...rest,
      headers,
      signal: controller.signal,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error((err as { detail?: string }).detail || res.statusText);
    }
    return res.json();
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new Error('הבקשה לקחה יותר מדי זמן — נסה שוב');
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
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
  profile_type: 'HOME_BUYER' | 'INVESTOR' | 'CASH_FLOW_MAXIMIZER';
  home_index: number;
  loan_term_years: number;
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

export function login(email: string, password: string, rememberMe: boolean): Promise<LoginRes> {
  return request<LoginRes>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email: email.trim(), password, remember_me: rememberMe }),
  });
}

export function register(body: {
  name: string;
  email: string;
  password: string;
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
  profile_type: User['profile_type'];
  home_index: number;
  loan_term_years: number;
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
  /** הודעת הקשר לפי פרופיל (Home Buyer / Investor / Cash Flow) */
  profile_area_message?: string;
}

export function getProperties(params?: {
  deal_type?: string;
  city?: string;
  limit?: number;
  view?: 'latest' | 'all';
}): Promise<Property[]> {
  const q: Record<string, string> = {};
  if (params?.deal_type) q.deal_type = params.deal_type;
  if (params?.city) q.city = params.city;
  if (params?.limit) q.limit = String(params.limit);
  if (params?.view) q.view = params.view;
  return request<Property[]>('/properties', { params: q }).then((r) => (Array.isArray(r) ? r : []));
}

export interface ScanStartResult {
  status: 'started' | 'already_running';
}

export interface ScanStatus {
  running: boolean;
  finished: boolean;
  message: string;
  total_found: number;
  total_matches: number;
  log: { time: string; level: string; message: string }[];
}

/** Fire-and-forget: returns immediately while the scan runs in the background. */
export function startScan(): Promise<ScanStartResult> {
  return request<ScanStartResult>('/scan', { method: 'POST' });
}

/** Poll this every 2 s to get the current Hebrew progress message.
 *  Uses a short 8 s timeout so stale polls don't block the UI. */
export function getScanStatus(): Promise<ScanStatus> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 8_000);
  const token = getToken();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = 'Bearer ' + token;
  return fetch(buildUrl('/scan/status'), { headers, signal: controller.signal })
    .then((r) => {
      clearTimeout(timer);
      if (!r.ok) throw new Error(r.statusText);
      return r.json() as Promise<ScanStatus>;
    })
    .catch((err) => {
      clearTimeout(timer);
      throw err;
    });
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
