import { useAuthStore } from '@/stores/auth'

const BASE = '/api'

async function request<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const auth = useAuthStore()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  }
  if (auth.token) {
    headers['Authorization'] = `Bearer ${auth.token}`
  }

  const resp = await fetch(`${BASE}${path}`, { ...options, headers })
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}))
    const detail = (body as any).detail || resp.statusText
    const err = new Error(detail) as any
    err.status = resp.status
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
  })
}