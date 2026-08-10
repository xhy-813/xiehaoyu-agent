<template>
  <div class="chat-fullscreen">
    <header class="cf-bar">
      <div class="cf-left">
        <button class="cf-back" aria-label="会话列表" title="会话列表" @click="sidebarOpen = !sidebarOpen">
          <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
        </button>
        <button class="cf-back" aria-label="返回作品集" @click="goBack">
          <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5"/><path d="m12 19-7-7 7-7"/></svg>
          <span>返回作品集</span>
        </button>
        <div class="cf-title-group">
          <span class="cf-title">AI 问答助手 · 谢浩宇的数字分身</span>
          <span class="cf-subtitle">基于 LLM Agent · RAG 知识库 · Text2SQL · 自动可视化</span>
        </div>
      </div>
      <div class="cf-right">
        <button
          v-if="chat.messages.length > 0 && !chat.isStreaming"
          class="cf-clear"
          aria-label="清空对话"
          title="清空对话"
          @click="chat.clearChat()"
        >
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
          <span>清空</span>
        </button>
        <div class="cf-status">
          <span class="cf-dot" aria-hidden="true" />
          在线
        </div>
      </div>
    </header>
    <div class="cf-main">
      <SessionSidebar v-show="sidebarOpen" @close="sidebarOpen = false" @select="onSidebarSelect" />
      <div class="cf-body">
        <ChatWidget>
          <template #empty>
            <WelcomeScreen
              :disabled="chat.isStreaming"
              @ask="ask"
            />
          </template>
        </ChatWidget>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import ChatWidget from '@/components/chat/ChatWidget.vue'
import WelcomeScreen from '@/components/chat/WelcomeScreen.vue'
import SessionSidebar from '@/components/chat/SessionSidebar.vue'
import { useChatStore } from '@/stores/chat'
import { useSessionsStore } from '@/stores/sessions'
import { useEscapeKey } from '@/composables/useMediaQuery'

const router = useRouter()
const chat = useChatStore()
const sessions = useSessionsStore()

// 桌面 ≥768px 默认展开，移动端默认收起
const isDesktop = window.matchMedia('(min-width: 768px)').matches
const sidebarOpen = ref(isDesktop)

onMounted(() => {
  sessions.fetchList()
})

function onSidebarSelect() {
  // 移动端选择会话后自动收起侧栏
  if (!window.matchMedia('(min-width: 768px)').matches) {
    sidebarOpen.value = false
  }
}

function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push({ path: '/', hash: '#ai-chat' })
  }
}
useEscapeKey(goBack)

function ask(q: string) {
  if (chat.isStreaming) return
  chat.sendMessage(q)
}
</script>

<style scoped>
.chat-fullscreen {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-base);
}
.cf-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.85rem 1.75rem;
  border-bottom: 1px solid var(--chat-bar-border);
  background: var(--chat-bar-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: var(--chat-bar-shadow);
  animation: cfSlideDown 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes cfSlideDown {
  from { transform: translateY(-100%); opacity: 0; }
  to   { transform: translateY(0); opacity: 1; }
}
.cf-left {
  display: flex;
  align-items: center;
  gap: 1rem;
  min-width: 0;
}
.cf-back {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-family: var(--font-mono);
  font-size: 0.78rem;
  color: var(--text-2);
  padding: 0.5rem 0.85rem;
  border: 1px solid transparent;
  border-radius: 7px;
  background: transparent;
  cursor: pointer;
  white-space: nowrap;
  transition: color 0.25s ease, background 0.25s ease, border-color 0.25s ease, transform 0.25s ease;
}
.cf-back:hover {
  color: var(--accent-strong);
  background: var(--back-btn-hover-bg);
  border-color: var(--back-btn-hover-border);
  transform: translateX(-2px);
}
.cf-title-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.cf-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-bright);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cf-subtitle {
  font-family: var(--font-mono);
  font-size: 0.66rem;
  color: var(--text-2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cf-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
}
.cf-clear {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--text-3);
  padding: 0.4rem 0.7rem;
  border: 1px solid transparent;
  border-radius: 7px;
  background: transparent;
  cursor: pointer;
  transition: color 0.2s, background 0.2s, border-color 0.2s;
}
.cf-clear:hover {
  color: #ff7b7b;
  background: rgba(255, 100, 100, 0.06);
  border-color: rgba(255, 100, 100, 0.2);
}
.cf-status {
  display: flex;
  align-items: center;
  gap: 7px;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--accent-strong);
  flex-shrink: 0;
}
.cf-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-strong);
  animation: pulse-glow 2s infinite;
}
.cf-main {
  flex: 1;
  min-height: 0;
  display: flex;
}
.cf-body {
  flex: 1;
  min-height: 0;
  min-width: 0;
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
}
@media (max-width: 640px) {
  .cf-bar { padding: 0.6rem 0.8rem; }
  .cf-subtitle { display: none; }
  .cf-title { font-size: 0.85rem; }
  .cf-back span { display: none; }
}
@media (max-width: 767px) {
  .session-sidebar {
    position: absolute;
    z-index: 30;
    height: calc(100% - 57px);
    box-shadow: 4px 0 24px rgba(0, 0, 0, 0.25);
  }
}

</style>
