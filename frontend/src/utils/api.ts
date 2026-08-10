import { getUserId } from './user'

/** 统一 fetch 封装：自动注入 X-User-Id；非 2xx 抛带后端 detail 的 Error。 */
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(path, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': getUserId(),
      ...(init?.headers ?? {}),
    },
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(err.detail || `请求失败（${resp.status}）`)
  }
  return resp.json()
}
