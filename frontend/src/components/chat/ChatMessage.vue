<template>
  <div class="chat-message" :class="[message.role, { 'chat-message-enter': animate }]">
    <!-- Avatar -->
    <div class="msg-avatar">
      <n-avatar v-if="message.role === 'user'" :size="34" round :style="{ background: 'linear-gradient(135deg, #6366f1, #818cf8)' }">
        <n-icon size="18"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg></n-icon>
      </n-avatar>
      <div v-else class="ai-avatar">
        <n-icon size="20" color="#63e2b7">
          <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
        </n-icon>
      </div>
    </div>

    <!-- Content -->
    <div class="msg-body">
      <div class="msg-role">
        {{ message.role === 'user' ? '你' : 'Xiehaoyu-Agent' }}
        <span class="msg-time">{{ formatTime(message.timestamp) }}</span>
      </div>

      <!-- Text content -->
      <div v-if="message.content" class="msg-bubble">
        <div class="msg-content" :class="{ 'streaming-cursor': isStreaming }" v-html="renderedContent" />
        <div v-if="!isStreaming && message.content" class="msg-actions">
          <n-button text size="tiny" @click="copyContent" title="复制">
            <template #icon><n-icon size="14"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg></n-icon></template>
          </n-button>
        </div>
      </div>
      <div v-else class="msg-loading">
        <n-spin :size="16" />
      </div>

      <!-- Step tags -->
      <div v-if="message.steps" class="msg-footer">
        <n-tag size="tiny" :bordered="false" type="info" round>
          {{ message.steps }} 步
        </n-tag>
        <n-tag v-for="t in message.tools" :key="t" size="tiny" :bordered="false" round>
          {{ toolLabel(t) }}
        </n-tag>
      </div>

      <!-- Inline result: data + chart + trace for assistant messages -->
      <div v-if="message.role === 'assistant' && message.trace && message.trace.length > 0 && !isStreaming" class="inline-result">
        <!-- Chart -->
        <div v-if="chartJson" class="ir-section">
          <div class="ir-section-header">
            <n-icon size="16" color="#63e2b7"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg></n-icon>
            <span>图表</span>
            <n-tag size="tiny" :bordered="false" type="success">{{ chartTypeLabel }}</n-tag>
          </div>
          <div class="ir-chart-wrap">
            <ChartRenderer :figure-json="chartJson" />
          </div>
        </div>

        <!-- Data table: always visible -->
        <div v-if="dataArtifact" class="ir-section">
          <div class="ir-section-header">
            <n-icon size="16" color="#63a4ff"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M4 6h16v2H4zm0 5h16v2H4zm0 5h16v2H4z"/></svg></n-icon>
            <span>数据表</span>
            <n-tag size="tiny" :bordered="false">{{ rowsCols }}</n-tag>
          </div>
          <n-collapse :default-expanded-names="[]">
            <n-collapse-item title="SQL 语句" name="sql">
              <n-code :code="dataArtifact.sql || '(无)'" language="sql" :word-wrap="true" />
            </n-collapse-item>
          </n-collapse>
          <div class="ir-table-wrap">
            <n-data-table :columns="columns" :data="rows" :max-height="260" size="small" :bordered="false" striped virtual-scroll />
          </div>
        </div>

        <!-- Trace: collapsible -->
        <n-collapse :default-expanded-names="[]">
          <n-collapse-item name="trace">
            <template #header>
              <div class="ir-section-header">
                <n-icon size="16" color="#f59e0b"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg></n-icon>
                <span>执行轨迹</span>
                <n-tag size="tiny" :bordered="false" type="warning">{{ message.trace.length }} 步</n-tag>
              </div>
            </template>
            <div class="ir-trace">
              <div v-for="(step, i) in message.trace" :key="i" class="irt-step">
                <div class="irt-line">
                  <div class="irt-dot" :style="{ background: stepColor(step.tool) }" />
                  <div v-if="i < message.trace.length - 1" class="irt-connector" />
                </div>
                <div class="irt-body">
                  <div class="irt-header">
                    <n-tag size="tiny" :bordered="false" :type="tagType(step.tool)" round>{{ toolLabel(step.tool) }}</n-tag>
                    <span class="irt-num">Step {{ i + 1 }}</span>
                  </div>
                  <div class="irt-summary">{{ step.summary }}</div>
                </div>
              </div>
            </div>
          </n-collapse-item>
        </n-collapse>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import ChartRenderer from '@/components/result/ChartRenderer.vue'
import type { ChatMessage } from '@/stores/chat'

const TOOL_LABELS: Record<string, string> = {
  query_data: '查询数据', visualize: '生成图表',
  introduce_me: '检索知识库', explain_result: '解读结果',
}
const TAG_MAP: Record<string, 'info' | 'success' | 'warning' | 'default'> = {
  query_data: 'info', visualize: 'success', introduce_me: 'warning', explain_result: 'default',
}
const STEP_COLORS: Record<string, string> = {
  query_data: '#63a4ff', visualize: '#63e2b7', introduce_me: '#ffb74d', explain_result: '#ce93d8',
}
const CHART_LABELS: Record<string, string> = {
  indicator: '指标卡', line: '折线图', bar: '柱状图', scatter: '散点图', table: '表格',
}

function toolLabel(t: string) { return TOOL_LABELS[t] || t }
function tagType(t: string) { return TAG_MAP[t] || 'default' }
function stepColor(t: string) { return STEP_COLORS[t] || '#888' }

const props = defineProps<{ message: ChatMessage; isStreaming?: boolean }>()

const animate = ref(true)

const md = new MarkdownIt({
  html: false, linkify: true, breaks: true,
  highlight(str: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      try { return hljs.highlight(str, { language: lang }).value } catch { /* */ }
    }
    return ''
  },
})

const renderedContent = computed(() => md.render(props.message.content))

function formatTime(ts: number) {
  return new Date(ts).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
async function copyContent() {
  try { await navigator.clipboard.writeText(props.message.content) } catch { /* */ }
}

// --- Result data from trace ---
const trace = computed(() => props.message.trace || [])

const dataArtifact = computed(() => {
  for (let i = trace.value.length - 1; i >= 0; i--) {
    const a = trace.value[i].artifact
    if (a?.df_json) return a
  }
  return null
})
const chartJson = computed(() => {
  for (let i = trace.value.length - 1; i >= 0; i--) {
    const a = trace.value[i].artifact
    if (a?.figure_json) return a.figure_json
  }
  return null
})
const columns = computed(() => {
  const cols = dataArtifact.value?.df_columns || []
  return cols.map((c: string) => ({ title: c, key: c, ellipsis: { tooltip: true }, minWidth: 80, maxWidth: 300 }))
})
const rows = computed(() => {
  if (!dataArtifact.value?.df_json) return []
  try { return JSON.parse(dataArtifact.value.df_json) } catch { return [] }
})
const rowsCols = computed(() => {
  const a = dataArtifact.value
  return a?.df_shape ? `${a.df_shape.rows}×${a.df_shape.cols}` : '--'
})
const chartTypeLabel = computed(() => {
  const t = trace.value.find(s => s.artifact?.chart_type)?.artifact?.chart_type || ''
  return CHART_LABELS[t] || t || '--'
})

onMounted(() => {
  setTimeout(() => { animate.value = false }, 300)
})
</script>

<style scoped>
.chat-message {
  display: flex;
  gap: 0.8rem;
  padding: 1rem 0;
}
.chat-message.user { flex-direction: row-reverse; }
.msg-avatar { flex-shrink: 0; padding-top: 2px; }
.ai-avatar {
  width: 34px; height: 34px; border-radius: 50%;
  background: rgba(99, 226, 183, 0.12);
  display: flex; align-items: center; justify-content: center;
}
.msg-body { flex: 1; min-width: 0; }
.msg-role {
  font-size: 0.76rem; font-weight: 600; color: #777;
  margin-bottom: 0.3rem; display: flex; align-items: center; gap: 0.5rem;
}
.chat-message.user .msg-role { flex-direction: row-reverse; }
.msg-time { font-weight: 400; font-size: 0.7rem; color: #555; }
.msg-bubble { position: relative; border-radius: 12px; overflow: hidden; }
.chat-message.user .msg-bubble {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(129, 140, 248, 0.1));
  border: 1px solid rgba(99, 102, 241, 0.15); padding: 0.7rem 1rem;
}
.msg-content {
  font-size: 0.92rem; line-height: 1.7; color: #e0e0e0; word-break: break-word;
}
.msg-content :deep(p) { margin: 0.5em 0; }
.msg-content :deep(p:first-child) { margin-top: 0; }
.msg-content :deep(pre) { border-radius: 10px; overflow-x: auto; margin: 0.6em 0; background: rgba(0,0,0,0.3) !important; }
.msg-content :deep(code) { font-size: 0.84rem; }
.msg-content :deep(blockquote) { border-left: 3px solid #63e2b7; padding-left: 0.8rem; margin: 0.5em 0; color: #999; }
.msg-content :deep(a) { color: #63e2b7; text-decoration: none; }
.msg-content :deep(a:hover) { text-decoration: underline; }
.msg-content :deep(table) { border-collapse: collapse; margin: 0.5em 0; width: 100%; }
.msg-content :deep(th), .msg-content :deep(td) { border: 1px solid rgba(255,255,255,0.1); padding: 0.4rem 0.7rem; font-size: 0.85rem; text-align: left; }
.msg-content :deep(th) { background: rgba(255,255,255,0.05); }
.msg-content :deep(ul), .msg-content :deep(ol) { padding-left: 1.5em; }
.msg-content :deep(li) { margin: 0.2em 0; }
.msg-loading { padding: 0.5rem 0; }
.msg-actions { display: flex; justify-content: flex-end; margin-top: 0.4rem; opacity: 0; transition: opacity 0.2s; }
.msg-bubble:hover .msg-actions { opacity: 1; }
.msg-footer { display: flex; gap: 0.35rem; flex-wrap: wrap; margin-top: 0.5rem; }

/* Inline result */
.inline-result {
  margin-top: 0.6rem;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  overflow: hidden;
}
.ir-section {
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.ir-section:last-child {
  border-bottom: none;
}
.ir-section-header {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.55rem 0.8rem; font-size: 0.83rem; color: #ccc;
  background: rgba(255,255,255,0.02);
}
.ir-table-wrap {  }
.ir-chart-wrap { padding: 0.5rem; }
.ir-chart-inner { min-height: 300px; }

/* Inline trace timeline */
.ir-trace { padding: 0.5rem 0.8rem; }
.irt-step { display: flex; gap: 0.5rem; }
.irt-line { display: flex; flex-direction: column; align-items: center; width: 12px; flex-shrink: 0; }
.irt-dot { width: 8px; height: 8px; border-radius: 50%; margin-top: 5px; }
.irt-connector { width: 1px; flex: 1; background: rgba(255,255,255,0.08); margin: 3px 0; }
.irt-body { flex: 1; padding: 0.2rem 0 0.7rem; }
.irt-header { display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.2rem; }
.irt-num { font-size: 0.68rem; color: #555; }
.irt-summary { font-size: 0.78rem; color: #aaa; line-height: 1.4; word-break: break-word; }
</style>