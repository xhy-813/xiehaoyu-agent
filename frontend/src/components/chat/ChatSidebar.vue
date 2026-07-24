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
      <div class="sh-logo">
        <n-icon size="26" color="#63e2b7">
          <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
        </n-icon>
      </div>
      <div>
        <div class="sh-title">Xiehaoyu-Agent</div>
        <div class="sh-subtitle">个人智能体工作台</div>
      </div>
    </div>

    <!-- Status -->
    <div class="sidebar-body">
      <div class="sb-section">
        <div class="sb-label">会话状态</div>
        <div class="status-grid">
          <div class="status-item">
            <span class="si-val">{{ chat.messages.length }}</span>
            <span class="si-lbl">消息</span>
          </div>
          <div class="status-item">
            <span class="si-val">{{ chat.currentTrace.length }}</span>
            <span class="si-lbl">步骤</span>
          </div>
          <div class="status-item">
            <span class="si-val" :style="{ color: chat.isStreaming ? '#f59e0b' : '#63e2b7' }">
              {{ chat.isStreaming ? '●' : '●' }}
            </span>
            <span class="si-lbl">{{ chat.isStreaming ? '处理中' : '就绪' }}</span>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="sb-section">
        <div class="sb-label">操作</div>
        <div class="action-list">
          <n-button
            block
            secondary
            size="small"
            @click="chat.clearChat()"
            :disabled="chat.messages.length === 0"
          >
            <template #icon>
              <n-icon size="16"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 4h-3.5l-1-1h-5l-1 1H5v2h14V4zM6 7v12c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6z"/></svg></n-icon>
            </template>
            清空对话
          </n-button>
        </div>
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

defineEmits<{ close: [] }>()

const router = useRouter()
const auth = useAuthStore()
const chat = useChatStore()

function handleLogout() {
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
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.sh-logo {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(99, 226, 183, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.sh-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #e0e0e0;
  line-height: 1.2;
}
.sh-subtitle {
  font-size: 0.7rem;
  color: #666;
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
  color: #555;
  margin-bottom: 0.55rem;
  font-weight: 600;
}

/* Status grid */
.status-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.4rem;
}
.status-item {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 8px;
  padding: 0.5rem 0.4rem;
  text-align: center;
}
.si-val {
  display: block;
  font-size: 0.95rem;
  font-weight: 700;
  color: #e0e0e0;
}
.si-lbl {
  display: block;
  font-size: 0.65rem;
  color: #666;
  margin-top: 0.1rem;
}

/* Actions */
.action-list {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

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
  background: rgba(255, 255, 255, 0.05);
  color: #666;
}
.logout-btn {
  width: 100%;
  justify-content: center;
}
</style>