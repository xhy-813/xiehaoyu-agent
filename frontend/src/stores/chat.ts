import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { sseChatStream, type Artifact, type SSEChatEvent } from '@/utils/sse'
import { useAuthStore } from '@/stores/auth'
import { CHART_LABELS } from '@/utils/tool-constants'
import type { AvatarState } from '@/components/shared/AnimatedAvatar.vue'

export interface ToolTrace {
  tool: string
  args: Record<string, unknown>
  summary: string
  artifact: Artifact | null
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  steps?: number
  tools?: string[]
  trace?: ToolTrace[]  // 该消息对应的执行轨迹
  timestamp: number
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const currentTrace = ref<ToolTrace[]>([])
  const isStreaming = ref(false)
  const streamError = ref<string | null>(null)
  const abortController = ref<AbortController | null>(null)

  // ── Avatar state ──────────────────────────────────────────────────────────

  const avatarState = ref<AvatarState>('idle')
  let avatarTimer: ReturnType<typeof setTimeout> | null = null

  /** 当前 trace 中是否包含数据或图表 */
  const hasData = computed(() => {
    const trace = _activeTrace()
    return trace.some(t => t.artifact?.df_json || t.artifact?.figure_json)
  })

  function setAvatarState(state: AvatarState, duration?: number) {
    avatarState.value = state
    if (avatarTimer) { clearTimeout(avatarTimer); avatarTimer = null }
    if (duration) {
      avatarTimer = setTimeout(() => {
        avatarState.value = 'idle'
        avatarTimer = null
      }, duration)
    }
  }

  // 监听 streaming → 结束
  watch(isStreaming, (now, prev) => {
    if (prev && !now) {
      // streaming 刚刚结束
      if (streamError.value) {
        setAvatarState('error', 3000)
      } else if (hasData.value) {
        setAvatarState('presenting', 3500)
      } else {
        setAvatarState('answering', 2500)
      }
    }
  })

  // 监听错误
  watch(streamError, (err) => {
    if (err && !isStreaming.value) {
      setAvatarState('error', 3000)
    }
  })

  // ── Artifact getters (shared across ChatMessage, ResultData, ResultSummary, ResultChart) ──

  /** Trace entries for the currently-streaming message, or the last completed one. */
  function _activeTrace(): ToolTrace[] {
    if (currentTrace.value.length > 0) return currentTrace.value
    // Fall back to the last assistant message's trace (after streaming completes)
    for (let i = messages.value.length - 1; i >= 0; i--) {
      const t = messages.value[i].trace
      if (t && t.length > 0) return t
    }
    return []
  }

  /** Last artifact containing df_json (backwards search). */
  const dataArtifact = computed<Artifact | null>(() => {
    const trace = _activeTrace()
    for (let i = trace.length - 1; i >= 0; i--) {
      const a = trace[i].artifact
      if (a?.df_json) return a
    }
    return null
  })

  /** Last artifact containing figure_json. */
  const chartArtifact = computed<Artifact | null>(() => {
    const trace = _activeTrace()
    for (let i = trace.length - 1; i >= 0; i--) {
      const a = trace[i].artifact
      if (a?.figure_json) return a
    }
    return null
  })

  const chartJson = computed(() => chartArtifact.value?.figure_json || null)

  const rowsCols = computed(() => {
    const a = dataArtifact.value
    return a?.df_shape ? `${a.df_shape.rows}×${a.df_shape.cols}` : '--'
  })

  const chartTypeLabel = computed(() => {
    const t = chartArtifact.value?.chart_type || ''
    return CHART_LABELS[t] || t || '--'
  })

  // ── Actions ──────────────────────────────────────────────────────────────

  async function sendMessage(question: string) {
    const auth = useAuthStore()
    if (!auth.token || isStreaming.value) return

    // Abort any existing stream
    if (abortController.value) {
      abortController.value.abort()
      abortController.value = null
    }

    abortController.value = new AbortController()

    // 1. Add user message
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: question,
      timestamp: Date.now(),
    }
    messages.value.push(userMsg)

    // 2. Add placeholder assistant message
    const assistantMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
    }
    messages.value.push(assistantMsg)

    // 3. Reset trace
    currentTrace.value = []
    isStreaming.value = true
    streamError.value = null
    setAvatarState('thinking')

    // 4. Start SSE stream
    try {
      await sseChatStream(question, auth.token, {
        onToolEnd: (data: SSEChatEvent['data']) => {
          currentTrace.value.push({
            tool: data.tool || '',
            args: (data.args || {}) as Record<string, unknown>,
            summary: data.summary || '',
            artifact: data.artifact || null,
          })
        },
        onFinalAnswer: (data: SSEChatEvent['data']) => {
          assistantMsg.content = data.answer || ''
          assistantMsg.steps = currentTrace.value.length
          assistantMsg.tools = currentTrace.value.map((t) => t.tool)
          assistantMsg.trace = [...currentTrace.value]
        },
        onError: (err: string) => {
          streamError.value = err
          assistantMsg.content = `执行失败：${err}`
        },
      }, abortController.value.signal)
    } catch (err: any) {
      if (err.name === 'AbortError') {
        assistantMsg.content = assistantMsg.content || '请求已取消'
      } else {
        streamError.value = err.message || '未知错误'
        assistantMsg.content = `执行失败：${err.message || '未知错误'}`
      }
    } finally {
      isStreaming.value = false
      abortController.value = null
    }
  }

  function clearChat() {
    messages.value = []
    currentTrace.value = []
    streamError.value = null
    avatarState.value = 'idle'
    if (avatarTimer) { clearTimeout(avatarTimer); avatarTimer = null }
  }

  return {
    messages,
    currentTrace,
    isStreaming,
    streamError,
    avatarState,
    hasData,
    dataArtifact,
    chartArtifact,
    chartJson,
    rowsCols,
    chartTypeLabel,
    sendMessage,
    clearChat,
  }
})