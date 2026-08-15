import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { sseChatStream, SSEStreamError, type Artifact, type SSEChatEvent } from '@/utils/sse'
import { uuid } from '@/utils/uuid'
import type { AvatarState } from '@/components/shared/AnimatedAvatar.vue'
import { useSessionsStore } from './sessions'

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
  const slowStream = ref(false)  // T4-10：流式超过 60s 的中间态提示开关
  let slowTimer: ReturnType<typeof setTimeout> | null = null

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

    // 提前置位：防 await ensureSession 期间重入导致双建会话（终审修订）；
    // 原有 step 3 的 isStreaming.value = true 保留即可（幂等）
    isStreaming.value = true

    // 幂等主流程：先确保持有 session_id，再发 chat（避免自动重试造成重复会话）
    const sessions = useSessionsStore()
    let sessionId: string
    try {
      sessionId = await sessions.ensureSession()
    } catch {
      streamError.value = '创建会话失败，请检查网络后重试'
      isStreaming.value = false
      return
    }

    wasStopped.value = false

    // Abort any existing stream
    if (abortController.value) {
      abortController.value.abort()
      abortController.value = null
    }

    abortController.value = new AbortController()

    // 1. Add user message
    const userMsg: ChatMessage = {
      id: uuid(),
      role: 'user',
      content: question,
      timestamp: Date.now(),
    }
    messages.value.push(userMsg)

    // 2. Add placeholder assistant message
    const assistantMsg: ChatMessage = {
      id: uuid(),
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

    // 08-09 方案 T4-10：流式超过 60s 无结果时给出中间态提示，避免用户干等
    slowStream.value = false
    if (slowTimer) clearTimeout(slowTimer)
    slowTimer = setTimeout(() => { slowStream.value = true }, 60_000)

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
        onError: (err: string, status?: number) => {
          streamError.value = err
          // 08-09 方案 T4-3：429 限流的后端文案已友好化，直接透传，
          // 不加「执行失败：」前缀（避免看起来像系统崩溃）
          assistantMsg.content = status === 429 ? err : `执行失败：${err}`
        },
        onDone: () => {
          // 刷新列表排序/标题；标题由后端异步生成，5s 后再刷一次兜底
          sessions.fetchList()
          setTimeout(() => sessions.fetchList(), 5000)
        },
      }, abortController.value.signal, { sessionId })
    } catch (err: any) {
      if (err instanceof SSEStreamError && err.kind === 'timeout') {
        // 本地 180s 超时（后端可能仍在执行）：区别于用户主动停止（808 审查 M4）
        streamError.value = '请求超时'
        assistantMsg.content = '响应时间较长，请稍后重试。'
        assistantMsg.error = true
      } else if (err instanceof SSEStreamError && err.kind === 'stream') {
        streamError.value = '连接中断'
        assistantMsg.content = '连接中断，请重试。'
        assistantMsg.error = true
      } else if (err.name === 'AbortError') {
        assistantMsg.content = assistantMsg.content || '请求已取消'
      } else if (err.message?.includes('fetch') || err.message?.includes('network') || err.message?.includes('Network')) {
        streamError.value = '网络错误'
        assistantMsg.content = '网络连接失败，请检查网络后重试。'
        assistantMsg.error = true
      } else {
        streamError.value = err.message || 'AI 服务异常'
        assistantMsg.content = `AI 服务暂时不可用，请稍后重试。`
        assistantMsg.error = true
      }
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
      if (slowTimer) { clearTimeout(slowTimer); slowTimer = null }
      slowStream.value = false
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
    wasStopped.value = false
    avatarState.value = 'idle'
    if (avatarTimer) { clearTimeout(avatarTimer); avatarTimer = null }
    // 清空 = 开始新会话
    useSessionsStore().currentId = null
  }

  /** 回放历史会话：消息 + trace 原样灌入，InlineResult 零改动渲染（设计文档 §5） */
  async function loadSession(id: string) {
    if (isStreaming.value) return
    const sessions = useSessionsStore()
    let data: Awaited<ReturnType<typeof sessions.loadReplay>>
    try {
      data = await sessions.loadReplay(id)
    } catch {
      streamError.value = '加载会话失败，请重试'
      return
    }
    messages.value = data.messages.map((m) => ({
      id: String(m.id),
      role: m.role,
      content: m.content,
      steps: m.steps ?? undefined,
      tools: m.tools ?? undefined,
      trace: m.trace ?? undefined,
      timestamp: new Date(m.created_at.replace(' ', 'T')).getTime() || Date.now(),
    }))
    currentTrace.value = []
    streamError.value = null
    wasStopped.value = false  // 复位停止标记，避免回放会话末条消息幻影显示「已停止生成」
    sessions.currentId = id
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
    slowStream,
    sendMessage,
    stopStreaming,
    clearChat,
    loadSession,
  }
})
