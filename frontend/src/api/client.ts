import { useAuthStore } from '@/stores/auth'

const BASE = '/api'

export interface ApiError extends Error {
  status: number
}

async function request<T = unknown>(
  path: string,
  options: RequestInit & { skipAuthRedirect?: boolean } = {},
): Promise<T> {
  const { skipAuthRedirect, ...fetchOptions } = options
  const auth = useAuthStore()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(fetchOptions.headers as Record<string, string> | undefined),
  }
  if (auth.token) {
    headers['Authorization'] = `Bearer ${auth.token}`
  }

  const resp = await fetch(`${BASE}${path}`, {
    ...fetchOptions,
    headers,
    signal: fetchOptions.signal ?? AbortSignal.timeout(30000),
  })
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}))
    const detail = (body as Record<string, unknown>).detail || resp.statusText
    const err = new Error(String(detail)) as ApiError
    err.status = resp.status

    // Global 401 handling: clear auth and redirect to login.
    // 登录请求自身的 401 是"凭证错误"（由调用方内联展示），不重定向。
    if (resp.status === 401 && !skipAuthRedirect) {
      auth.logout()
      window.location.href = '/login'
    }

    throw err
  }
  return resp.json()
}

export const api = { request }

export interface LoginResponse {
  access_token: string
  token_type: string
}

export async function loginApi(accessCode: string): Promise<LoginResponse> {
  return request<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ access_code: accessCode }),
    skipAuthRedirect: true,
  })
}