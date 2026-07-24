<template>
  <div v-if="chat.currentTrace.length > 0" class="result-trace">
    <div class="trace-timeline">
      <div
        v-for="(entry, i) in chat.currentTrace"
        :key="i"
        class="trace-step"
        :class="{ 'is-last': i === chat.currentTrace.length - 1 }"
      >
        <!-- Timeline dot -->
        <div class="step-line">
          <div class="step-dot" :style="{ background: stepColor(entry.tool) }" />
          <div v-if="i < chat.currentTrace.length - 1" class="step-connector" />
        </div>
        <!-- Step content -->
        <div class="step-card">
          <div class="step-header">
            <n-tag size="tiny" :bordered="false" :type="tagType(entry.tool)" round>
              {{ toolLabel(entry.tool) }}
            </n-tag>
            <span class="step-num">Step {{ i + 1 }}</span>
          </div>
          <div class="step-summary">{{ entry.summary || '执行中...' }}</div>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="empty-state">
    <n-text depth="3">暂无轨迹，提问后执行记录将在此展示</n-text>
  </div>
</template>

<script setup lang="ts">
import { useChatStore } from '@/stores/chat'

const chat = useChatStore()

const TOOL_LABELS: Record<string, string> = {
  query_data: '查询数据',
  visualize: '生成图表',
  introduce_me: '检索知识库',
  explain_result: '解读结果',
}

function toolLabel(tool: string) {
  return TOOL_LABELS[tool] || tool
}

const TAG_MAP: Record<string, 'info' | 'success' | 'warning' | 'default'> = {
  query_data: 'info',
  visualize: 'success',
  introduce_me: 'warning',
  explain_result: 'default',
}

function tagType(tool: string) {
  return TAG_MAP[tool] || 'default'
}

const STEP_COLORS: Record<string, string> = {
  query_data: '#63a4ff',
  visualize: '#63e2b7',
  introduce_me: '#ffb74d',
  explain_result: '#ce93d8',
}

function stepColor(tool: string) {
  return STEP_COLORS[tool] || '#888'
}
</script>

<style scoped>
.result-trace {
  padding: 0.5rem 0;
}
.empty-state {
  text-align: center;
  padding: 1.5rem 0;
}

/* Timeline */
.trace-timeline {
  display: flex;
  flex-direction: column;
}
.trace-step {
  display: flex;
  gap: 0.6rem;
}
.step-line {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 14px;
  flex-shrink: 0;
}
.step-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-top: 6px;
  box-shadow: 0 0 8px currentColor;
}
.step-connector {
  width: 1px;
  flex: 1;
  background: rgba(255, 255, 255, 0.08);
  margin: 4px 0;
}
.step-card {
  flex: 1;
  padding: 0.4rem 0 0.9rem;
}
.step-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.3rem;
}
.step-num {
  font-size: 0.72rem;
  color: #555;
}
.step-summary {
  font-size: 0.8rem;
  color: #aaa;
  line-height: 1.45;
  word-break: break-word;
}
</style>