<template>
  <aside class="session-sidebar">
    <div class="ss-head">
      <button class="ss-new" @click="onNew">
        <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 5v14"/><path d="M5 12h14"/></svg>
        新会话
      </button>
      <button class="ss-close" aria-label="收起侧栏" @click="$emit('close')">«</button>
    </div>

    <div class="ss-search">
      <input
        v-model="keyword"
        class="ss-search-input"
        type="text"
        placeholder="搜索会话…"
        @input="onSearchInput"
      />
    </div>

    <div class="ss-list">
      <div
        v-for="s in displayList"
        :key="s.id"
        class="ss-item"
        :class="{ active: s.id === sessions.currentId }"
        :title="chat.isStreaming ? '生成回答中，点击切换将中断' : undefined"
        @click="onSelect(s.id)"
      >
        <input
          v-if="renamingId === s.id"
          v-model="renameText"
          class="ss-rename-input"
          @keyup.enter="submitRename(s.id)"
          @keyup.esc="renamingId = null"
          @blur="submitRename(s.id)"
          @click.stop
        />
        <template v-else>
          <span class="ss-title">{{ s.title || '新会话' }}</span>
          <span class="ss-time">{{ formatRelativeTime(s.updated_at) }}</span>
          <span class="ss-actions">
            <button class="ss-action" title="重命名" @click.stop="startRename(s)">✎</button>
            <NPopconfirm @positive-click="onDelete(s.id)">
              <template #trigger>
                <button class="ss-action ss-action-danger" title="删除" @click.stop>✕</button>
              </template>
              确定删除该会话？此操作不可恢复。
            </NPopconfirm>
          </span>
        </template>
      </div>
      <div v-if="displayList.length === 0" class="ss-empty">
        {{ keyword ? '没有匹配的会话' : '暂无历史会话' }}
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { NPopconfirm } from 'naive-ui'
import { useSessionsStore, type SessionSummary } from '@/stores/sessions'
import { useChatStore } from '@/stores/chat'
import { formatRelativeTime } from '@/utils/time'

const emit = defineEmits<{ close: []; select: [] }>()

const sessions = useSessionsStore()
const chat = useChatStore()

const keyword = ref('')
const searchResults = ref<SessionSummary[]>([])
const renamingId = ref<string | null>(null)
const renameText = ref('')

const displayList = computed(() => (keyword.value.trim() ? searchResults.value : sessions.list))

let searchTimer: ReturnType<typeof setTimeout> | null = null
function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    const q = keyword.value.trim()
    searchResults.value = q ? await sessions.search(q) : []
  }, 300)
}

async function onNew() {
  // 同 T3：开始新会话也是一种切换，流式期间需先确认中断
  if (chat.isStreaming) {
    if (!window.confirm('当前正在生成回答，开始新会话将中断本次回答，是否继续？')) return
    chat.stopStreaming()
  }
  chat.clearChat()
  emit('select')
}

async function onSelect(id: string) {
  if (id === sessions.currentId) return
  // 08-09 方案 T3：流式期间切换会话 = 确认后中断当前流（参考 CopilotKit 切换 thread 自动 abortRun）
  if (chat.isStreaming) {
    if (!window.confirm('当前正在生成回答，切换会话将中断本次回答，是否继续？')) return
    chat.stopStreaming()
  }
  await chat.loadSession(id)
  emit('select')
}

function startRename(s: SessionSummary) {
  renamingId.value = s.id
  renameText.value = s.title || ''
}

async function submitRename(id: string) {
  if (renamingId.value !== id) return  // Esc 已取消后移除 input 触发的 stale blur，直接忽略
  const title = renameText.value.trim()
  renamingId.value = null
  if (title) await sessions.rename(id, title)
}

async function onDelete(id: string) {
  const wasCurrent = id === sessions.currentId
  await sessions.remove(id)
  if (wasCurrent) chat.clearChat()
}
</script>

<style scoped>
.session-sidebar {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--chat-bar-border);
  background: var(--chat-bar-bg);
  min-height: 0;
}
.ss-head {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
}
.ss-new {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  padding: 0.5rem;
  font-size: 0.8rem;
  color: var(--accent-strong);
  border: 1px solid var(--chat-bar-border);
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}
.ss-new:hover {
  background: var(--back-btn-hover-bg);
  border-color: var(--back-btn-hover-border);
}
.ss-close {
  padding: 0.4rem 0.5rem;
  color: var(--text-3);
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 6px;
}
.ss-close:hover { color: var(--text-bright); background: var(--back-btn-hover-bg); }
.ss-search { padding: 0 0.75rem 0.6rem; }
.ss-search-input {
  width: 100%;
  padding: 0.45rem 0.6rem;
  font-size: 0.78rem;
  color: var(--text-bright);
  background: var(--bg-base);
  border: 1px solid var(--chat-bar-border);
  border-radius: 7px;
  outline: none;
}
.ss-search-input:focus { border-color: var(--accent-strong); }
.ss-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 0.5rem 0.75rem;
}
.ss-item {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0.55rem 0.6rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}
.ss-item:hover { background: var(--back-btn-hover-bg); }
.ss-item.active { background: var(--back-btn-hover-bg); outline: 1px solid var(--back-btn-hover-border); }
.ss-title {
  font-size: 0.8rem;
  color: var(--text-bright);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 2.8rem;
}
.ss-time {
  font-family: var(--font-mono);
  font-size: 0.64rem;
  color: var(--text-3);
}
.ss-actions {
  position: absolute;
  top: 0.45rem;
  right: 0.45rem;
  display: none;
  gap: 0.2rem;
}
.ss-item:hover .ss-actions { display: inline-flex; }
.ss-action {
  padding: 0.15rem 0.3rem;
  font-size: 0.7rem;
  color: var(--text-3);
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 5px;
}
.ss-action:hover { color: var(--text-bright); background: var(--bg-base); }
.ss-action-danger:hover { color: #ff7b7b; }
.ss-rename-input {
  width: 100%;
  padding: 0.3rem 0.45rem;
  font-size: 0.8rem;
  color: var(--text-bright);
  background: var(--bg-base);
  border: 1px solid var(--accent-strong);
  border-radius: 6px;
  outline: none;
}
.ss-empty {
  padding: 1.5rem 0.5rem;
  text-align: center;
  font-size: 0.75rem;
  color: var(--text-3);
}
</style>
