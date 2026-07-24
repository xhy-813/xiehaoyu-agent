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
  citations?: Array<{ source: string; heading: string; score: number }>
}

export interface SSECallbacks {
  onPlannerDecision?: (data: SSEChatEvent['data']) => void
  onToolEnd?: (data: SSEChatEvent['data']) => void
  onFinalAnswer?: (data: SSEChatEvent['data']) => void
  onError?: (message: string) => void
  onDone?: () => void
}

export async function sseChatStream(
  question: string,
  token: string,
  callbacks: SSECallbacks,
): Promise<void> {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ question }),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: '请求失败' }))
    callbacks.onError?.(err.detail || '请求失败')
    return
  }

  const reader = response.body!.getReader()
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
        // skip malformed JSON lines
      }
    }
  }
}