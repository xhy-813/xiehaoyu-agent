<template>
  <div v-if="latestTrace" class="summary-row">
    <div class="metric-card">
      <div class="metric-icon" style="color: #63a4ff">
        <n-icon size="16"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M4 6h16v2H4zm0 5h16v2H4zm0 5h16v2H4z"/></svg></n-icon>
      </div>
      <div class="metric-label">数据</div>
      <div class="metric-value">{{ rowsCols }}</div>
    </div>
    <div class="metric-card">
      <div class="metric-icon" style="color: #63e2b7">
        <n-icon size="16"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg></n-icon>
      </div>
      <div class="metric-label">图表</div>
      <div class="metric-value">{{ chartTypeLabel }}</div>
    </div>
    <div class="metric-card">
      <div class="metric-icon" style="color: #f59e0b">
        <n-icon size="16"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg></n-icon>
      </div>
      <div class="metric-label">步骤</div>
      <div class="metric-value">{{ chat.currentTrace.length }}</div>
    </div>
  </div>
  <div v-else class="empty-state">
    <n-text depth="3" class="empty-text">提问后结果将在此展示</n-text>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useChatStore } from '@/stores/chat'

const chat = useChatStore()

const latestTrace = computed(() => {
  if (chat.currentTrace.length === 0) return null
  return chat.currentTrace[chat.currentTrace.length - 1]
})

const rowsCols = computed(() => chat.rowsCols)
const chartTypeLabel = computed(() => chat.chartTypeLabel)
</script>

<style scoped>
.summary-row {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}
.metric-card {
  flex: 1;
  background: rgba(255, 255, 255, 0.035);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  padding: 0.55rem 0.5rem;
  text-align: center;
}
.metric-icon {
  margin-bottom: 0.2rem;
}
.metric-label {
  font-size: 0.64rem;
  color: #777;
  margin-bottom: 0.1rem;
}
.metric-value {
  font-size: 0.82rem;
  font-weight: 700;
  color: #e0e0e0;
}
.empty-state {
  text-align: center;
  padding: 1.5rem 0;
}
.empty-text {
  font-size: 0.82rem;
}
</style>