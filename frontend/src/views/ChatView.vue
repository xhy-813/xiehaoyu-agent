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
        <NPopover trigger="click" placement="bottom-end">
          <template #trigger>
            <button class="cf-action" aria-label="联系我" title="联系我">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
              <span>联系我</span>
            </button>
          </template>
          <div class="cf-contact">
            <div class="cf-contact-row">
              <span class="cf-contact-label">邮箱</span>
              <button class="cf-contact-value" @click="copy(profile.email)">
                {{ profile.email }}<em v-if="copied === profile.email">已复制 ✓</em>
              </button>
            </div>
            <div class="cf-contact-row">
              <span class="cf-contact-label">微信</span>
              <button class="cf-contact-value" @click="copy(profile.wechat)">
                {{ profile.wechat }}<em v-if="copied === profile.wechat">已复制 ✓</em>
              </button>
            </div>
            <div class="cf-contact-tip">点击复制 · 添加微信请备注来意</div>
          </div>
        </NPopover>
        <a class="cf-action" href="/resume.pdf" download="谢浩宇-简历.pdf" title="下载简历 PDF">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          <span>下载简历</span>
        </a>
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
      <!-- T4-8：移动端 overlay 抽屉的遮罩，点击外部收起 -->
      <div v-if="!isDesktop && sidebarOpen" class="cf-scrim" @click="sidebarOpen = false" />
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
import { NPopover } from 'naive-ui'
import ChatWidget from '@/components/chat/ChatWidget.vue'
import WelcomeScreen from '@/components/chat/WelcomeScreen.vue'
import SessionSidebar from '@/components/chat/SessionSidebar.vue'
import { useChatStore } from '@/stores/chat'
import { useSessionsStore } from '@/stores/sessions'
import { useMediaQuery, useEscapeKey } from '@/composables/useMediaQuery'
import { profile } from '@/data/profile'

const router = useRouter()
const chat = useChatStore()
const sessions = useSessionsStore()

// 桌面 ≥768px 默认展开，移动端默认收起（T4-8：移动端 overlay 抽屉模式）
const isDesktop = useMediaQuery('(min-width: 768px)')
const sidebarOpen = ref(window.matchMedia('(min-width: 768px)').matches)

// T4-7：联系方式一键复制的「已复制」反馈
const copied = ref('')
async function copy(text: string) {
  try { await navigator.clipboard.writeText(text) } catch { /* 剪贴板不可用（非 HTTPS/权限拒绝）时静默 */ }
  copied.value = text
  setTimeout(() => { if (copied.value === text) copied.value = '' }, 1500)
}

onMounted(() => {
  sessions.fetchList()
})

function onSidebarSelect() {
  // 移动端选择会话后自动收起侧栏
  if (!isDesktop.value) {
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
/* T4-7 转化出口按钮（联系我 / 下载简历） */
.cf-action {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--text-2);
  padding: 0.4rem 0.7rem;
  border: 1px solid var(--chat-bar-border);
  border-radius: 7px;
  background: transparent;
  cursor: pointer;
  text-decoration: none;
  white-space: nowrap;
  transition: color 0.2s, background 0.2s, border-color 0.2s;
}
.cf-action:hover {
  color: var(--accent-strong);
  background: var(--back-btn-hover-bg);
  border-color: var(--back-btn-hover-border);
}
.cf-contact {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  min-width: 240px;
}
.cf-contact-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}
.cf-contact-label {
  font-size: 0.75rem;
  color: var(--text-3);
  flex-shrink: 0;
}
.cf-contact-value {
  font-family: var(--font-mono);
  font-size: 0.78rem;
  color: var(--text-bright);
  border: none;
  background: transparent;
  cursor: copy;
  padding: 0.2rem 0.3rem;
  border-radius: 5px;
  transition: background 0.2s;
}
.cf-contact-value:hover { background: var(--back-btn-hover-bg); }
.cf-contact-value em {
  font-style: normal;
  font-size: 0.7rem;
  color: var(--accent-strong);
  margin-left: 0.4rem;
}
.cf-contact-tip {
  font-size: 0.68rem;
  color: var(--text-3);
  border-top: 1px dashed var(--border);
  padding-top: 0.4rem;
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
  .cf-action span { display: none; }
}
/* T4-8：移动端侧栏改为 overlay 抽屉（参考 CopilotKit desktop docked / mobile overlay 双模式） */
@media (max-width: 767px) {
  .cf-main { position: relative; }
  .session-sidebar {
    position: absolute;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 30;
    box-shadow: 4px 0 24px rgba(0, 0, 0, 0.25);
  }
  .cf-scrim {
    position: absolute;
    inset: 0;
    z-index: 25;
    background: rgba(0, 0, 0, 0.4);
  }
}

</style>
