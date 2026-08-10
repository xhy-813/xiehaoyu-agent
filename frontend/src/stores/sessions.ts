import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/utils/api'
import type { ToolTrace } from './chat'

export interface SessionSummary {
  id: string
  title: string | null
  updated_at: string
}

export interface ReplayMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  steps: number | null
  tools: string[] | null
  trace: ToolTrace[] | null
  created_at: string
}

export interface ReplayResponse {
  session: { id: string; title: string | null; created_at: string; updated_at: string }
  messages: ReplayMessage[]
}

export const useSessionsStore = defineStore('sessions', () => {
  const list = ref<SessionSummary[]>([])
  const currentId = ref<string | null>(null)

  async function fetchList() {
    const data = await api<{ sessions: SessionSummary[] }>('/api/sessions')
    list.value = data.sessions
  }

  async function create(): Promise<string> {
    const data = await api<{ session_id: string }>('/api/sessions', {
      method: 'POST',
      body: '{}',
    })
    currentId.value = data.session_id
    await fetchList()
    return data.session_id
  }

  /** 幂等主流程（设计文档 §5）：发送前调用，无当前会话则先创建。 */
  async function ensureSession(): Promise<string> {
    if (!currentId.value) {
      await create()
    }
    return currentId.value!
  }

  async function rename(id: string, title: string) {
    await api(`/api/sessions/${id}`, { method: 'PATCH', body: JSON.stringify({ title }) })
    await fetchList()
  }

  async function remove(id: string) {
    await api(`/api/sessions/${id}`, { method: 'DELETE' })
    if (currentId.value === id) currentId.value = null
    await fetchList()
  }

  async function search(q: string): Promise<SessionSummary[]> {
    const data = await api<{ sessions: SessionSummary[] }>(
      `/api/sessions/search?q=${encodeURIComponent(q)}`,
    )
    return data.sessions
  }

  async function loadReplay(id: string): Promise<ReplayResponse> {
    return api<ReplayResponse>(`/api/sessions/${id}`)
  }

  return {
    list,
    currentId,
    fetchList,
    create,
    ensureSession,
    rename,
    remove,
    search,
    loadReplay,
  }
})
