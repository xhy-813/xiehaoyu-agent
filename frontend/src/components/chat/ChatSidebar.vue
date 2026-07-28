<template>
  <n-layout-sider
    bordered
    collapse-mode="width"
    :collapsed-width="0"
    :width="260"
    show-trigger="bar"
    class="chat-sidebar"
  >
    <!-- Header -->
    <div class="sidebar-header">
      <AnimatedAvatar state="idle" :size="40" />
      <div>
        <div class="sh-title">Xiehaoyu-Agent</div>
        <div class="sh-subtitle">个人智能体工作台</div>
      </div>
    </div>

    <!-- Body -->
    <div class="sidebar-body">
      <!-- 快捷提问（功能导航，分组） -->
      <div class="sb-section" v-for="g in QUICK_QUESTION_GROUPS" :key="g.name">
        <div class="sb-label">{{ g.name }}</div>
        <div class="nav-list">
          <button
            v-for="q in g.questions"
            :key="q.question"
            class="nav-item"
            :disabled="chat.isStreaming"
            @click="handleNav(q.question)"
          >
            <span class="nav-dot" :style="{ background: q.color }" />
            <span class="nav-text">{{ q.label }}</span>
            <span class="nav-question truncate">{{ q.question }}</span>
          </button>
        </div>
      </div>

      <!-- 会话状态（精简为单行） -->
      <div class="sb-section">
        <div class="sb-label">会话状态</div>
        <div class="status-line">
          <span
            class="status-dot"
            role="status"
            :aria-label="chat.isStreaming ? '处理中' : '就绪'"
            :style="{ background: chat.isStreaming ? '#d97706' : '#0b7a55' }"
          />
          <span class="status-text">
            {{ chat.isStreaming ? '处理中' : '就绪' }} · {{ chat.messages.length }} 条消息 · {{ chat.currentTrace.length }} 步
          </span>
        </div>
      </div>

      <!-- 操作 -->
      <div class="sb-section">
        <div class="sb-label">操作</div>
        <n-button
          block
          secondary
          size="small"
          :disabled="chat.messages.length === 0"
          @click="chat.clearChat()"
        >
          <template #icon>
            <n-icon size="16"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 4h-3.5l-1-1h-5l-1 1H5v2h14V4zM6 7v12c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6z"/></svg></n-icon>
          </template>
          清空对话
        </n-button>
      </div>
    </div>

    <!-- Footer -->
    <div class="sidebar-footer">
      <n-divider style="margin: 0.5rem 0" />
      <div class="tech-badges">
        <span class="tech-badge">LangGraph</span>
        <span class="tech-badge">DeepSeek</span>
        <span class="tech-badge">ChromaDB</span>
      </div>
      <n-button text size="tiny" @click="handleLogout" class="logout-btn">
        <template #icon>
          <n-icon size="14"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/></svg></n-icon>
        </template>
        退出登录
      </n-button>
    </div>
  </n-layout-sider>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import AnimatedAvatar from '@/components/shared/AnimatedAvatar.vue'
import { QUICK_QUESTION_GROUPS } from '@/utils/quick-questions'

const emit = defineEmits<{ close: [] }>()

const router = useRouter()
const auth = useAuthStore()
const chat = useChatStore()

function handleNav(question: string) {
  if (chat.isStreaming) return
  chat.sendMessage(question)
  emit('close')   // 移动端点选后收起侧栏；桌面端 close 无人监听无副作用
}

function handleLogout() {
  chat.clearChat()
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.chat-sidebar {
  display: flex;
  flex-direction: column;
}

/* Header */
.sidebar-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.1rem 1.2rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}
.sh-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-1);
  line-height: 1.2;
}
.sh-subtitle {
  font-size: 0.7rem;
  color: var(--text-3);
  margin-top: 1px;
}

/* Body */
.sidebar-body {
  flex: 1;
  padding: 1rem 1.2rem;
  overflow-y: auto;
}
.sb-section {
  margin-bottom: 1.2rem;
}
.sb-label {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-3);
  margin-bottom: 0.55rem;
  font-weight: 600;
}

/* Nav list */
.nav-list { display: flex; flex-direction: column; gap: 2px; }
.nav-item {
  display: flex; align-items: center; gap: 0.55rem;
  width: 100%;
  padding: 0.55rem 0.6rem;
  border: none; border-radius: 8px;
  background: transparent;
  cursor: pointer; text-align: left;
  transition: background 0.15s ease;
}
.nav-item:hover:not(:disabled) { background: rgba(0, 0, 0, 0.04); }
.nav-item:disabled { opacity: 0.5; cursor: not-allowed; }
.nav-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.nav-text { font-size: 0.875rem; font-weight: 600; color: var(--text-1); flex-shrink: 0; }
.nav-question { font-size: 0.75rem; color: var(--text-3); }

/* Status line */
.status-line { display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.2rem; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; }
.status-text { font-size: 0.8125rem; color: var(--text-2); }

/* Footer */
.sidebar-footer {
  padding: 0 1.2rem 1rem;
}
.tech-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  justify-content: center;
  margin-bottom: 0.5rem;
}
.tech-badge {
  font-size: 0.64rem;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.04);
  color: var(--text-2);
}
.logout-btn {
  width: 100%;
  justify-content: center;
}
</style>