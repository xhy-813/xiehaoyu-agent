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
  /** status：HTTP 状态码（仅连接即失败的场景有值，如 429；08-09 方案 T4-3） */
  onError?: (message: string, status?: number) => void
  onDone?: () => void
}

export interface SSEOptions {
  /** 会话 ID；调用方（chat store）负责先 ensureSession 再传入 */
  sessionId?: string
}

import { getUserId } from './user'

const SSE_TIMEOUT_MS = 180_000  // 808 审查 M5：覆盖后端最坏合法时长（多步 LLM + SQL 重试 + polish），Nginx proxy_read_timeout 为 300s
const MAX_RETRIES = 3
const INITIAL_RETRY_DELAY_MS = 1000

/** SSE 流异常分类（808 审查 M4：修复重试逻辑错位）。
 *
 * - `connect`：连接未建立（DNS/拒连/断网）——请求未到达服务端，重试安全
 * - `stream`：流中途断开——服务端可能已完成整轮（LLM 已计费、消息已落库），重试会双烧，禁止重试
 * - `timeout`：本地 120s 超时——后端仍在执行，重试会双烧，禁止重试
 * - `aborted`：用户主动停止——不重试，原样上抛
 */
export class SSEStreamError extends Error {
  readonly kind: 'connect' | 'stream' | 'timeout' | 'aborted'
  constructor(kind: 'connect' | 'stream' | 'timeout' | 'aborted', message: string) {
    super(message)
    this.name = 'SSEStreamError'
    this.kind = kind
  }
}

async function _doStream(
  question: string,
  callbacks: SSECallbacks,
  signal?: AbortSignal,
  options: SSEOptions = {},
): Promise<void> {
  const controller = new AbortController()
  let timedOut = false
  let connected = false
  const timeoutId = setTimeout(() => { timedOut = true; controller.abort() }, SSE_TIMEOUT_MS)

  // Link external signal
  const onAbort = () => controller.abort()
  signal?.addEventListener('abort', onAbort, { once: true })

  try {
    let response: Response
    try {
      response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': getUserId(),
        },
        body: JSON.stringify({ question, session_id: options.sessionId ?? null }),
        signal: controller.signal,
      })
    } catch (err) {
      // 分类：用户停止 > 本地超时 > 连接失败
      if (signal?.aborted) throw err
      if (timedOut) throw new SSEStreamError('timeout', '请求超时')
      throw new SSEStreamError('connect', '网络连接失败')
    }
    connected = true

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: '请求失败' }))
      callbacks.onError?.(err.detail || '请求失败', response.status)
      return
    }

    if (!response.body) {
      callbacks.onError?.('服务器返回了空的响应体')
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    try {
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
    } catch (err) {
      // 读取阶段失败：流已建立，重试会重复消耗 LLM 额度
      if (signal?.aborted) throw err
      if (timedOut) throw new SSEStreamError('timeout', '请求超时')
      if (err instanceof SSEStreamError) throw err
      throw new SSEStreamError(connected ? 'stream' : 'connect', '连接中断')
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
  let lastStatus: number | undefined

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    if (attempt > 0) {
      const delay = INITIAL_RETRY_DELAY_MS * Math.pow(2, attempt - 1)
      console.warn(`[SSE] Retry ${attempt}/${MAX_RETRIES} after ${delay}ms`)
      await new Promise(resolve => setTimeout(resolve, delay))
    }

    let done = false
    let errorMsg = ''

    try {
      await _doStream(
        question,
        {
          ...callbacks,
          // 终审修订：链式调用调用方 onDone——原写法 {...callbacks, onDone: ...} 会把
          // 调用方传入的 onDone 整体覆盖（既有隐患），Task 10 的会话列表刷新依赖它
          onDone: () => { done = true; callbacks.onDone?.() },
          onError: (msg, status) => { errorMsg = msg; lastStatus = status },
        },
        signal,
        options,
      )
    } catch (err) {
      // 808 审查 M4：只有"连接未建立"才可安全重试；超时/中途断开/用户停止
      // 直接上抛（此时重试会让后端重复执行整轮 Agent，双倍消耗 LLM 额度）
      if (err instanceof SSEStreamError && err.kind === 'connect') {
        lastError = err.message
        continue
      }
      throw err
    }

    if (done) return  // stream completed successfully
    if (!errorMsg) return  // no error, just ended (e.g. abort)

    lastError = errorMsg
    // 808 审查 M4：应用层错误（429 限流、404 会话不存在等）是确定性结果，
    // 立即透传给用户，不做无效重试；只有"空响应体"（流未开始）可安全重试
    if (errorMsg === '服务器返回了空的响应体') continue
    break
  }

  callbacks.onError?.(lastError || '请求失败，已重试多次', lastStatus)
}
