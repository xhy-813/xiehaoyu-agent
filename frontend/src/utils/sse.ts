export interface SSEChatEvent {
  type: 'planner_decision' | 'tool_end' | 'final_answer' | 'error'
  node: string
  data: {
    answer?: string
    steps?: number
    tool?: string
    args?: Record<string, unknown>
    summary?: string
    artifact?: Artifact | null
    next_action?: string
    next_tool?: string
    step?: number
    message?: string
  }
}

export interface Artifact {
  sql?: string
  df_json?: string
  df_shape?: { rows: number; cols: number }
  df_columns?: string[]
  figure_json?: string
  chart_type?: string
  answer?: string
  citations?: Array<{
    source: string
    heading: string
    distance: number    // cosine distance，越小越相关
    similarity: number  // 1 - distance，越大越相关
  }>
}

export interface SSECallbacks {
  onPlannerDecision?: (data: SSEChatEvent['data']) => void
  onToolEnd?: (data: SSEChatEvent['data']) => void
  onFinalAnswer?: (data: SSEChatEvent['data']) => void
  onError?: (message: string) => void
  onDone?: () => void
}

export interface SSEOptions {
  /** 会话 ID；调用方（chat store）负责先 ensureSession 再传入 */
  sessionId?: string
}

import { getUserId } from './user'

const SSE_TIMEOUT_MS = 120_000
const MAX_RETRIES = 3
const INITIAL_RETRY_DELAY_MS = 1000

async function _doStream(
  question: string,
  callbacks: SSECallbacks,
  signal?: AbortSignal,
  options: SSEOptions = {},
): Promise<void> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), SSE_TIMEOUT_MS)

  // Link external signal
  const onAbort = () => controller.abort()
  signal?.addEventListener('abort', onAbort, { once: true })

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Id': getUserId(),
      },
      body: JSON.stringify({ question, session_id: options.sessionId ?? null }),
      signal: controller.signal,
    })

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: '请求失败' }))
      callbacks.onError?.(err.detail || '请求失败')
      return
    }

    if (!response.body) {
      callbacks.onError?.('服务器返回了空的响应体')
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const raw = line.slice(6).trim()
        if (raw === '[DONE]') {
          callbacks.onDone?.()
          return
        }

        try {
          const event: SSEChatEvent = JSON.parse(raw)
          switch (event.type) {
            case 'planner_decision':
              callbacks.onPlannerDecision?.(event.data)
              break
            case 'tool_end':
              callbacks.onToolEnd?.(event.data)
              break
            case 'final_answer':
              callbacks.onFinalAnswer?.(event.data)
              break
            case 'error':
              callbacks.onError?.(event.data.message || '未知错误')
              return
          }
        } catch {
          // Malformed JSON line — log it but don't crash the stream
          console.warn('[SSE] Failed to parse event:', raw.slice(0, 120))
        }
      }
    }
  } finally {
    clearTimeout(timeoutId)
    signal?.removeEventListener('abort', onAbort)
  }
}

export async function sseChatStream(
  question: string,
  callbacks: SSECallbacks,
  signal?: AbortSignal,
  options: SSEOptions = {},
): Promise<void> {
  let lastError = ''

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    if (attempt > 0) {
      const delay = INITIAL_RETRY_DELAY_MS * Math.pow(2, attempt - 1)
      console.warn(`[SSE] Retry ${attempt}/${MAX_RETRIES} after ${delay}ms`)
      await new Promise(resolve => setTimeout(resolve, delay))
    }

    let done = false
    let errorMsg = ''

    await _doStream(
      question,
      {
        ...callbacks,
        // 终审修订：链式调用调用方 onDone——原写法 {...callbacks, onDone: ...} 会把
        // 调用方传入的 onDone 整体覆盖（既有隐患），Task 10 的会话列表刷新依赖它
        onDone: () => { done = true; callbacks.onDone?.() },
        onError: (msg) => { errorMsg = msg },
      },
      signal,
      options,
    )

    if (done) return  // stream completed successfully
    if (!errorMsg) return  // no error, just ended (e.g. abort)

    lastError = errorMsg
    // Only retry on network errors, not on application errors
    if (errorMsg === '服务器返回了空的响应体') continue
  }

  callbacks.onError?.(lastError || '请求失败，已重试多次')
}
