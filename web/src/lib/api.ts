import { useAuthStore } from '../stores/authStore';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: unknown;
  params?: Record<string, string | number | undefined>;
  skipAuth?: boolean;
}

export class ApiError extends Error {
  status: number;
  statusText: string;
  body: unknown;

  constructor(status: number, statusText: string, body: unknown) {
    // F-WEB-09: surface RFC 7807 Problem Details 'title'/'detail' to callers
    // so components can show a meaningful message instead of the raw HTTP
    // status text. Validation 'detail' may be an array (kept on .body).
    let message = `API Error: ${status} ${statusText}`;
    if (body && typeof body === 'object') {
      const b = body as Record<string, unknown>;
      const detail = b.detail;
      const title = b.title;
      if (typeof detail === 'string' && detail.length) {
        message = detail;
      } else if (typeof title === 'string' && title.length) {
        message = title;
      }
    }
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.statusText = statusText;
    this.body = body;
  }
}

function buildUrl(path: string, params?: Record<string, string | number | undefined>): string {
  const url = new URL(`${API_BASE}${path}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    });
  }
  return url.toString();
}

export function getAccessToken(): string | null {
  try {
    const stored = localStorage.getItem('saw-auth');
    if (stored) {
      const parsed = JSON.parse(stored);
      return parsed.state?.accessToken ?? null;
    }
  } catch {
    // ignore
  }
  return null;
}

// F-AUTH-02 / F-WEB-03: refresh an expired access token once before bouncing
// the user to /login. Without this, a silently-expired 30-min access token
// caused in-flight form edits to be discarded by the hard redirect. A single
// in-flight refresh promise dedups concurrent 401s.
let refreshInFlight: Promise<string | null> | null = null;

export async function refreshAccessToken(): Promise<string | null> {
  if (refreshInFlight) return refreshInFlight;
  refreshInFlight = (async () => {
    try {
      const stored = localStorage.getItem('saw-auth');
      const refreshToken: string | null = stored
        ? JSON.parse(stored)?.state?.refreshToken ?? null
        : null;
      if (!refreshToken) return null;
      const res = await fetch(buildUrl('/api/auth/refresh'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!res.ok) return null;
      const data = await res.json();
      if (!data?.access_token) return null;
      useAuthStore.getState().setTokens(data.access_token, data.refresh_token ?? refreshToken);
      return data.access_token as string;
    } catch {
      return null;
    }
  })();
  try {
    return await refreshInFlight;
  } finally {
    refreshInFlight = null;
  }
}

// F-WEB-03: on a 401, try to refresh once and retry the original request.
// Returns the retried response on success, or null if the session is truly
// gone (caller should log out + redirect). Headers are mutable here.
async function retryAfterRefresh(
  url: string,
  method: string,
  headers: HeadersInit,
  buildBody: () => BodyInit | undefined,
): Promise<Response | null> {
  const newToken = await refreshAccessToken();
  if (!newToken) return null;
  const retryHeaders = { ...(headers as Record<string, string>), Authorization: `Bearer ${newToken}` };
  const retry = await fetch(url, { method, headers: retryHeaders, body: buildBody() });
  if (retry.status === 401) return null;
  return retry;
}

function bailSession(): never {
  useAuthStore.getState().logout();
  if (window.location.pathname !== '/login') {
    window.location.href = '/login';
  }
  throw new ApiError(401, 'Unauthorized', { message: 'Session expired' });
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, params, skipAuth = false } = options;
  const url = buildUrl(path, params);

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  // Attach JWT token if available
  if (!skipAuth) {
    const token = getAccessToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  const response = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  // F-WEB-03: on 401, try to refresh the access token and retry once
  // before discarding in-flight work / redirecting to /login.
  if (response.status === 401 && !skipAuth && !path.includes('/auth/')) {
    const retry = await retryAfterRefresh(url, method, headers, () =>
      body ? JSON.stringify(body) : undefined,
    );
    if (retry) {
      if (!retry.ok) {
        let errorBody: unknown;
        try { errorBody = await retry.json(); } catch { errorBody = null; }
        throw new ApiError(retry.status, retry.statusText, errorBody);
      }
      return retry.json();
    }
    bailSession();
  }

  if (!response.ok) {
    let errorBody: unknown;
    try {
      errorBody = await response.json();
    } catch {
      try {
        errorBody = await response.text();
      } catch {
        errorBody = null;
      }
    }
    throw new ApiError(response.status, response.statusText, errorBody);
  }

  return response.json();
}

async function requestForm<T>(path: string, formData: FormData): Promise<T> {
  const url = buildUrl(path);
  const headers: HeadersInit = {};

  const token = getAccessToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (response.status === 401 && !path.includes('/auth/')) {
    const retry = await retryAfterRefresh(url, 'POST', headers, () => formData);
    if (retry) {
      if (!retry.ok) {
        let errorBody: unknown;
        try { errorBody = await retry.json(); } catch { errorBody = null; }
        throw new ApiError(retry.status, retry.statusText, errorBody);
      }
      return retry.json();
    }
    bailSession();
  }

  if (!response.ok) {
    let errorBody: unknown;
    try { errorBody = await response.json(); } catch { errorBody = null; }
    throw new ApiError(response.status, response.statusText, errorBody);
  }

  return response.json();
}

export const api = {
  get: <T>(path: string, params?: Record<string, string | number | undefined>) =>
    request<T>(path, { method: 'GET', params }),

  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'POST', body }),

  postForm: <T>(path: string, formData: FormData) =>
    requestForm<T>(path, formData),

  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PUT', body }),

  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PATCH', body }),

  delete: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'DELETE', body }),
};