import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { sseChatStream, type Artifact, type SSEChatEvent } from '@/utils/sse'
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
  error?: boolean  // 是否为错误消息
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const currentTrace = ref<ToolTrace[]>([])
  const isStreaming = ref(false)
  const streamError = ref<string | null>(null)
  const abortController = ref<AbortController | null>(null)
  const currentTool = ref<string | null>(null)  // 流式期间正在执行的工具名
  const wasStopped = ref(false)

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

  // ── Actions ──────────────────────────────────────────────────────────────

  async function sendMessage(question: string) {
    if (isStreaming.value) return

    wasStopped.value = false

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
      await sseChatStream(question, {
        onPlannerDecision: (data: SSEChatEvent['data']) => {
          currentTool.value = data.next_action === 'call' ? (data.next_tool ?? null) : null
        },
        onToolEnd: (data: SSEChatEvent['data']) => {
          currentTool.value = null
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
      } else if (err.message?.includes('timeout') || err.message?.includes('超时')) {
        streamError.value = '请求超时'
        assistantMsg.content = '请求超时，请稍后重试。'
      } else if (err.message?.includes('fetch') || err.message?.includes('network') || err.message?.includes('Network')) {
        streamError.value = '网络错误'
        assistantMsg.content = '网络连接失败，请检查网络后重试。'
      } else {
        streamError.value = err.message || 'AI 服务异常'
        assistantMsg.content = `AI 服务暂时不可用，请稍后重试。`
      }
      assistantMsg.error = true
    } finally {
      // 停止/出错时兜底：把已收集的轨迹写回消息，保留停止前已完成的工具结果
      if (!assistantMsg.trace && currentTrace.value.length > 0) {
        assistantMsg.trace = [...currentTrace.value]
        assistantMsg.steps = currentTrace.value.length
        assistantMsg.tools = currentTrace.value.map((t) => t.tool)
      }
      isStreaming.value = false
      abortController.value = null
      currentTool.value = null
    }
  }

  function stopStreaming() {
    abortController.value?.abort()
    wasStopped.value = true
  }

  function clearChat() {
    messages.value = []
    currentTrace.value = []
    streamError.value = null
    currentTool.value = null
    avatarState.value = 'idle'
    if (avatarTimer) { clearTimeout(avatarTimer); avatarTimer = null }
  }

  return {
    messages,
    currentTrace,
    isStreaming,
    streamError,
    currentTool,
    avatarState,
    hasData,
    wasStopped,
    sendMessage,
    stopStreaming,
    clearChat,
  }
})