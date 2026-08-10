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
      <template v-if="message.content">
        <div class="msg-bubble-wrap" :class="{ 'msg-bubble-user': message.role === 'user', 'msg-bubble-assistant': message.role === 'assistant' }">
          <MessageBubble :content="message.content" :is-error="isError" :is-streaming="!!isStreaming" />
        </div>
      </template>
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

      <!-- Stopped hint -->
      <div v-if="wasStopped && message.content" class="msg-stopped-hint">
        已停止生成
        <button class="action-btn retry-btn" @click="retry">
          <n-icon size="14"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg></n-icon>
          重试
        </button>
      </div>

      <!-- Message actions (assistant, non-streaming): copy / retry / step tags -->
      <div v-if="message.role === 'assistant' && !isStreaming && message.content" class="msg-actions">
        <button class="action-btn" aria-label="复制内容" title="复制" @click="copyContent">
          <n-icon size="14"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg></n-icon>
        </button>
        <button v-if="isError && isLastAssistant" class="action-btn" aria-label="重试" title="重试" @click="retry">
          <n-icon size="14"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg></n-icon>
        </button>
        <template v-if="message.steps">
          <n-tag size="tiny" :bordered="false" type="info" round>{{ message.steps }} 步</n-tag>
          <n-tag v-for="t in message.tools" :key="t" size="tiny" :bordered="false" round>{{ toolLabel(t) }}</n-tag>
        </template>
      </div>

      <!-- Inline result: data + chart + trace for assistant messages -->
      <InlineResult v-if="message.role === 'assistant' && message.trace && message.trace.length > 0 && !isStreaming" :trace="message.trace" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import AnimatedAvatar from '@/components/shared/AnimatedAvatar.vue'
import MessageBubble from './MessageBubble.vue'
import InlineResult from './InlineResult.vue'
import type { ChatMessage } from '@/stores/chat'
import { useChatStore } from '@/stores/chat'
import { toolLabel, tagType, stepColor } from '@/utils/tool-constants'
import type { AvatarState } from '@/components/shared/AnimatedAvatar.vue'

const props = defineProps<{ message: ChatMessage; isStreaming?: boolean; wasStopped?: boolean }>()

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

const isLastAssistant = computed(() =>
  props.message.role === 'assistant' &&
  props.message === chat.messages[chat.messages.length - 1]
)

const avatarState = computed<AvatarState>(() => {
  if (!isLastAssistant.value) return 'idle'
  return chat.avatarState
})

const isError = computed(() => props.message.error === true)

function retry() {
  if (chat.isStreaming) return
  const idx = chat.messages.findIndex(m => m === props.message)
  if (idx === -1) return
  // 向上找到触发该回答的用户消息
  let userIdx = -1
  for (let i = idx - 1; i >= 0; i--) {
    if (chat.messages[i].role === 'user') { userIdx = i; break }
  }
  if (userIdx === -1) return
  const question = chat.messages[userIdx].content
  // 成对删除 user + assistant 再重发（08-09 方案 T4-2，对齐 CopilotKit regenerate 语义）
  chat.messages.splice(idx, 1)
  chat.messages.splice(userIdx, 1)
  chat.sendMessage(question)
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

/* Bubble wrapper */
.msg-bubble-wrap { position: relative; }
.msg-bubble-assistant {
  border-left: 2px solid rgba(100, 255, 218, 0.25);
  padding-left: 0.75rem;
  background: var(--msg-assistant-bg);
  border-radius: 0 8px 8px 0;
}
.msg-bubble-user {
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
.action-btn.retry-btn {
  color: var(--accent-strong);
  border: 1px solid var(--accent-border);
  background: rgba(100, 255, 218, 0.06);
  gap: 0.3rem;
  padding: 0 0.6rem;
  width: auto;
  border-radius: 6px;
}
.action-btn.retry-btn:hover {
  background: rgba(100, 255, 218, 0.12);
  border-color: var(--accent-strong);
}

.msg-stopped-hint {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  font-size: 0.78rem;
  color: var(--text-3);
}
.retry-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  color: var(--accent-strong);
  font-size: 0.78rem;
}

/* Live trace timeline (during streaming) */
.irt-step { display: flex; gap: 0.5rem; animation: fadeIn 0.25s ease-out; }
.irt-line { display: flex; flex-direction: column; align-items: center; width: 12px; flex-shrink: 0; }
.irt-dot { width: 8px; height: 8px; border-radius: 50%; margin-top: 5px; }
.irt-connector { width: 1px; flex: 1; background: var(--border); margin: 3px 0; }
.irt-body { flex: 1; padding: 0.2rem 0 0.7rem; }
.irt-header { display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.2rem; }
.irt-num { font-size: 0.68rem; color: var(--text-3); }
.irt-summary { font-size: 0.78rem; color: var(--text-2); line-height: 1.4; word-break: break-word; }

@media (max-width: 640px) {
  .chat-message { padding: 0.75rem 0; gap: 0.5rem; }
  .chat-message-consecutive { padding-top: 0.1rem; }
  .msg-bubble-user { max-width: 85%; }
  .msg-actions { opacity: 1; }
}
</style>