import type {
  DashboardStats,
  HeartStatus,
  SessionDetail,
  SessionListResponse,
  SessionQueryParams,
  TrendData,
} from '../types/dashboard';

const apiBase = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '');

const getDashboardHeaders = () => {
  const key = localStorage.getItem('dashboard_api_key');
  return { 'X-Dashboard-Key': key || '' };
};

async function fetchJson<T>(url: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export const verifyDashboardKey = (key: string): Promise<DashboardStats> =>
  fetchJson<DashboardStats>(`${apiBase}/dashboard/stats`, {
    headers: { 'X-Dashboard-Key': key },
  });

export const getStats = (): Promise<DashboardStats> =>
  fetchJson<DashboardStats>(`${apiBase}/dashboard/stats`, {
    headers: getDashboardHeaders(),
  });

export const getTrends = (period: 'daily' | 'weekly' = 'daily', days = 30): Promise<TrendData> =>
  fetchJson<TrendData>(`${apiBase}/dashboard/stats/trends?period=${period}&days=${days}`, {
    headers: getDashboardHeaders(),
  });

export const getSessions = (params: SessionQueryParams): Promise<SessionListResponse> => {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') qs.set(k, String(v));
  });
  return fetchJson<SessionListResponse>(`${apiBase}/dashboard/sessions?${qs.toString()}`, {
    headers: getDashboardHeaders(),
  });
};

export const getSessionDetail = (sessionId: string): Promise<SessionDetail> =>
  fetchJson<SessionDetail>(`${apiBase}/dashboard/sessions/${sessionId}`, {
    headers: getDashboardHeaders(),
  });

export const getHeartStatus = (): Promise<HeartStatus> =>
  fetchJson<HeartStatus>(`${apiBase}/dashboard/heart/status`, {
    headers: getDashboardHeaders(),
  });

export const toggleHeartStatus = (active: boolean): Promise<HeartStatus> =>
  fetchJson<HeartStatus>(`${apiBase}/dashboard/heart/status`, {
    method: 'PATCH',
    headers: { ...getDashboardHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ active }),
  });
