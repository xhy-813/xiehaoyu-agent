import { defineStore } from 'pinia'
import { ref } from 'vue'
import { sseChatStream, type Artifact, type SSEChatEvent } from '@/utils/sse'
import { useAuthStore } from '@/stores/auth'

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

  async function sendMessage(question: string) {
    const auth = useAuthStore()
    if (!auth.token) return

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
      })
    } catch (err: any) {
      streamError.value = err.message || '未知错误'
      assistantMsg.content = `执行失败：${err.message || '未知错误'}`
    } finally {
      isStreaming.value = false
    }
  }

  function clearChat() {
    messages.value = []
    currentTrace.value = []
    streamError.value = null
  }

  return {
    messages,
    currentTrace,
    isStreaming,
    streamError,
    sendMessage,
    clearChat,
  }
})