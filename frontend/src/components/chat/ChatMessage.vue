<template>
  <div
    class="chat-message"
    :class="[
      message.role,
      { 'chat-message-enter': animate && !isFirstAssistantMessage, 'chat-message-enter-first': animate && isFirstAssistantMessage, 'chat-message-consecutive': isConsecutive }
    ]"
  >
    <!-- Avatar -->
    <div class="msg-avatar">
      <n-avatar v-if="message.role === 'user'" :size="34" round :style="{ background: 'linear-gradient(135deg, #6366f1, #818cf8)' }">
        <n-icon size="18"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg></n-icon>
      </n-avatar>
      <AnimatedAvatar
        v-else
        :state="avatarState"
        :size="34"
      />
    </div>

    <!-- Content -->
    <div class="msg-body">
      <div class="msg-role">
        {{ message.role === 'user' ? '你' : 'Xiehaoyu-Agent' }}
        <span v-if="!isConsecutive" class="msg-time">{{ formatTime(message.timestamp) }}</span>
      </div>

      <!-- Text content -->
      <div v-if="message.content" class="msg-bubble" :class="{ 'msg-bubble-error': isError }">
        <div class="msg-content" :class="{ 'streaming-cursor': isStreaming || cursorFading, 'fade-out': cursorFading }" v-html="renderedContent" />
      </div>
      <div v-else class="msg-loading">
        <div class="loading-row">
          <n-spin :size="16" />
          <span class="msg-tool-status">
            <template v-if="isStreaming && chat.currentTool">
              正在调用「{{ toolLabel(chat.currentTool) }}」<span class="dot-anim">…</span>
            </template>
            <template v-else-if="isStreaming">
              正在思考<span class="dot-anim">…</span>
            </template>
          </span>
        </div>
        <!-- 实时轨迹（流式中，含流光） -->
        <div v-if="isStreaming && chat.currentTrace.length > 0" class="live-trace">
          <div v-for="(step, i) in chat.currentTrace" :key="i" class="irt-step">
            <div class="irt-line">
              <div class="irt-dot" :style="{ background: stepColor(step.tool) }" />
              <div
                v-if="i < chat.currentTrace.length - 1 || chat.currentTool"
                class="irt-connector"
                :class="{ flow: i === chat.currentTrace.length - 1 }"
              />
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
      </div>

      <!-- Message actions (assistant, non-streaming): copy / retry / step tags -->
      <div v-if="message.role === 'assistant' && !isStreaming && message.content" class="msg-actions">
        <button class="action-btn" aria-label="复制内容" title="复制" @click="copyContent">
          <n-icon size="14"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg></n-icon>
        </button>
        <button v-if="isError" class="action-btn" aria-label="重试" title="重试" @click="retry">
          <n-icon size="14"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg></n-icon>
        </button>
        <template v-if="message.steps">
          <n-tag size="tiny" :bordered="false" type="info" round>{{ message.steps }} 步</n-tag>
          <n-tag v-for="t in message.tools" :key="t" size="tiny" :bordered="false" round>{{ toolLabel(t) }}</n-tag>
        </template>
      </div>

      <!-- Inline result: data + chart + trace for assistant messages -->
      <div v-if="message.role === 'assistant' && message.trace && message.trace.length > 0 && !isStreaming" class="inline-result">
        <!-- Chart -->
        <div v-if="chartJson" class="ir-section">
          <div class="ir-section-header">
            <n-icon size="16" color="#64ffda"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg></n-icon>
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
            <n-icon size="16" color="#64b5f6"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M4 6h16v2H4zm0 5h16v2H4zm0 5h16v2H4z"/></svg></n-icon>
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
                <n-icon size="16" color="#ffb86c"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg></n-icon>
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
import { computed, ref, onMounted, watch } from 'vue'
import { useMessage } from 'naive-ui'
import ChartRenderer from '@/components/result/ChartRenderer.vue'
import AnimatedAvatar from '@/components/shared/AnimatedAvatar.vue'
import type { ChatMessage } from '@/stores/chat'
import { useChatStore } from '@/stores/chat'
import { CHART_LABELS, toolLabel, tagType, stepColor } from '@/utils/tool-constants'
import { findDataArtifact, findChartArtifact } from '@/utils/artifact'
import { renderMarkdown } from '@/utils/markdown'
import type { AvatarState } from '@/components/shared/AnimatedAvatar.vue'

const props = defineProps<{ message: ChatMessage; isStreaming?: boolean }>()

const chat = useChatStore()

const messageApi = useMessage()
const animate = ref(true)

const isConsecutive = computed(() => {
  const idx = chat.messages.indexOf(props.message as ChatMessage)
  if (idx <= 0) return false
  return chat.messages[idx - 1].role === props.message.role
})

const isFirstAssistantMessage = computed(() => {
  const idx = chat.messages.indexOf(props.message as ChatMessage)
  return idx === 0 || (props.message.role === 'assistant' &&
    chat.messages.slice(0, idx).every(m => m.role !== 'assistant'))
})

const cursorFading = ref(false)

watch(() => props.isStreaming, (now, prev) => {
  if (prev && !now) {
    cursorFading.value = true
    setTimeout(() => { cursorFading.value = false }, 300)
  }
})

const isLastAssistant = computed(() =>
  props.message.role === 'assistant' &&
  props.message === chat.messages[chat.messages.length - 1]
)

const avatarState = computed<AvatarState>(() => {
  if (!isLastAssistant.value) return 'idle'
  return chat.avatarState
})

const renderedContent = computed(() => renderMarkdown(props.message.content))

const isError = computed(() => props.message.error === true)

function retry() {
  if (isError.value) {
    const idx = chat.messages.findIndex(m => m === props.message)
    // Remove the failed message before retrying
    chat.messages.splice(idx, 1)
  }
  const idx = chat.messages.findIndex(m => m === props.message)
  const prevUser = chat.messages.slice(0, idx).reverse().find(m => m.role === 'user')
  if (prevUser && !chat.isStreaming) chat.sendMessage(prevUser.content)
}

function formatTime(ts: number) {
  return new Date(ts).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
async function copyContent() {
  try {
    await navigator.clipboard.writeText(props.message.content)
    messageApi.success('已复制到剪贴板')
  } catch {
    messageApi.warning('复制失败，请检查浏览器权限设置')
  }
}

// --- Result data from trace ---
const trace = computed(() => props.message.trace || [])

const dataArtifact = computed(() => findDataArtifact(trace.value))
const chartArtifact = computed(() => findChartArtifact(trace.value))
const chartJson = computed(() => chartArtifact.value?.figure_json || null)
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
  const t = chartArtifact.value?.chart_type || ''
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
  padding: 1.25rem 0;
  /* 悬浮时微亮背景，增加交互感 */
  border-radius: 12px;
  transition: background 0.2s;
}
.chat-message:hover {
  background: rgba(100, 255, 218, 0.015);
}
.chat-message.user { flex-direction: row-reverse; }
.chat-message-consecutive {
  padding-top: 0.15rem;
}
.chat-message-consecutive .msg-avatar {
  visibility: hidden;
}
.chat-message-consecutive .msg-role {
  display: none;
}
.msg-avatar { flex-shrink: 0; padding-top: 2px; }
.msg-body { flex: 1; min-width: 0; }
.msg-role {
  font-size: 0.75rem; font-weight: 600; color: var(--text-3);
  margin-bottom: 0.35rem; display: flex; align-items: center; gap: 0.5rem;
  letter-spacing: 0.03em;
}
.chat-message.user .msg-role { flex-direction: row-reverse; }
.msg-time { font-weight: 400; font-size: 0.72rem; color: var(--text-3); opacity: 0.65; }
.msg-bubble { position: relative; border-radius: 12px; overflow: hidden; overflow-wrap: break-word; }
.msg-bubble-error {
  background: rgba(255, 80, 80, 0.06);
  border: 1px solid rgba(255, 80, 80, 0.2);
  border-radius: 12px;
  padding: 0.6rem 0.9rem;
}
.msg-bubble-error .msg-content { color: #ff8080; }

/* 用户气泡：更饱和的描边渐变 */
.chat-message.user .msg-bubble {
  background: linear-gradient(
    135deg,
    rgba(100, 255, 218, 0.14) 0%,
    rgba(100, 255, 218, 0.06) 100%
  );
  border: 1px solid rgba(100, 255, 218, 0.18);
  box-shadow: 0 2px 12px rgba(100, 255, 218, 0.06), var(--msg-user-shadow);
  padding: 0.75rem 1rem;
  max-width: 72%;
  border-radius: 18px 18px 4px 18px;
  margin-left: auto;
}

/* 助手气泡：左侧 accent 竖线 */
.chat-message.assistant .msg-bubble {
  border-left: 2px solid rgba(100, 255, 218, 0.25);
  padding-left: 0.75rem;
  background: var(--msg-assistant-bg);
  border-radius: 0 8px 8px 0;
}

.msg-content {
  font-size: 0.875rem; line-height: 1.7; color: var(--text-1); word-break: break-word;
}
.msg-content :deep(p) { margin: 0.5em 0; }
.msg-content :deep(p:first-child) { margin-top: 0; }
.msg-content :deep(pre) { border-radius: 10px; overflow-x: auto; margin: 0.6em 0; }
.msg-content :deep(code) { font-size: 0.84rem; }
.msg-content :deep(blockquote) { border-left: 3px solid var(--accent-strong); padding-left: 0.8rem; margin: 0.5em 0; color: var(--text-2); }
.msg-content :deep(a) { color: var(--accent-strong); text-decoration: none; }
.msg-content :deep(a:hover) { text-decoration: underline; }
.msg-content :deep(table) { border-collapse: collapse; margin: 0.5em 0; width: 100%; }
.msg-content :deep(th), .msg-content :deep(td) { border: 1px solid var(--border); padding: 0.4rem 0.7rem; font-size: 0.85rem; text-align: left; }
.msg-content :deep(th) { background: var(--bg-subtle); }
.msg-content :deep(ul), .msg-content :deep(ol) { padding-left: 1.5em; }
.msg-content :deep(li) { margin: 0.2em 0; }
.msg-loading { padding: 0.5rem 0; }
.loading-row { display: flex; align-items: center; gap: 0.5rem; }
.dot-anim {
  display: inline-block;
  animation: dotFade 1.2s steps(3, end) infinite;
  letter-spacing: 0.05em;
}
@keyframes dotFade {
  0%   { opacity: 0; }
  33%  { opacity: 0.4; }
  66%  { opacity: 0.7; }
  100% { opacity: 1; }
}
.live-trace { margin-top: 0.6rem; }
.irt-connector.flow {
  background: linear-gradient(180deg, var(--accent-strong) 0%, rgba(136,146,176,0.25) 50%, var(--accent-strong) 100%);
  background-size: 100% 250%;
  animation: flowDown 1.2s linear infinite;
}
.msg-tool-status { font-size: 0.78rem; color: var(--tool-rag); }
.msg-actions {
  display: flex; align-items: center; gap: 0.4rem;
  margin-top: 0.5rem;
  opacity: 0;
  transition: opacity 0.2s;
}
.chat-message-enter-first {
  animation: fadeInUp 0.4s ease-out;
}
.chat-message-enter {
  animation: fadeIn 0.2s ease-out;
}
.chat-message:hover .msg-actions { opacity: 1; }
@media (hover: none) { .msg-actions { opacity: 1; } }
.action-btn {
  display: flex; align-items: center; justify-content: center;
  width: 26px; height: 26px;
  border: none; border-radius: 6px;
  background: transparent; color: var(--text-3);
  cursor: pointer; transition: background 0.2s, color 0.2s;
}
.action-btn:hover { background: rgba(255, 255, 255, 0.06); color: var(--text-1); }

/* Inline result */
.inline-result {
  margin-top: 0.75rem;
  border: 1px solid var(--border);
  background: var(--bg-card);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: var(--result-card-shadow);
}
.ir-section {
  border-bottom: 1px solid var(--border);
}
.ir-section:last-child {
  border-bottom: none;
}
.ir-section-header {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.55rem 0.8rem; font-size: 0.83rem; color: var(--text-2);
  background: var(--bg-subtle);
}
.ir-table-wrap {  }
.ir-chart-wrap { padding: 0.5rem; min-height: 300px; }
.ir-chart-inner { min-height: 300px; }

.ir-section :deep(.n-collapse-item__content-wrapper) {
  transition: max-height 0.3s ease, opacity 0.3s ease;
}

/* Inline trace timeline */
.ir-trace { padding: 0.5rem 0.8rem; }
.irt-step { display: flex; gap: 0.5rem; animation: fadeIn 0.25s ease-out; }
.irt-line { display: flex; flex-direction: column; align-items: center; width: 12px; flex-shrink: 0; }
.irt-dot { width: 8px; height: 8px; border-radius: 50%; margin-top: 5px; }
.irt-connector { width: 1px; flex: 1; background: var(--border); margin: 3px 0; }
.irt-body { flex: 1; padding: 0.2rem 0 0.7rem; }
.irt-header { display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.2rem; }
.irt-num { font-size: 0.68rem; color: var(--text-3); }
.irt-summary { font-size: 0.78rem; color: var(--text-2); line-height: 1.4; word-break: break-word; }
</style>