<template>
  <div class="chat-widget">
    <!-- Messages area -->
    <div class="messages-area" ref="messagesRef">
      <slot v-if="chat.messages.length === 0" name="empty" />
      <div v-else class="messages-list">
        <ChatMessage
          v-for="msg in chat.messages"
          :key="msg.id"
          :message="msg"
          :is-streaming="chat.isStreaming && msg === chat.messages[chat.messages.length - 1] && msg.role === 'assistant'"
          :was-stopped="chat.wasStopped && msg === chat.messages[chat.messages.length - 1] && msg.role === 'assistant'"
        />
      </div>

      <button
        v-if="showScrollButton"
        class="scroll-to-bottom"
        aria-label="回到底部"
        @click="scrollToBottom"
      >
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </button>
    </div>

    <!-- Input area -->
    <div class="input-area">
      <ChatInput
        :disabled="chat.isStreaming"
        :streaming="chat.isStreaming"
        @send="handleSend"
        @stop="chat.stopStreaming"
      />
      <p class="privacy-note">对话记录仅保存 30 天，到期自动删除，请勿输入敏感个人信息</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { watch, nextTick, ref, onMounted, onBeforeUnmount } from 'vue'
import ChatMessage from './ChatMessage.vue'
import ChatInput from './ChatInput.vue'
import { useChatStore } from '@/stores/chat'

const chat = useChatStore()
const messagesRef = ref<HTMLElement>()

async function handleSend(question: string) {
  await chat.sendMessage(question)
}

// Auto-scroll to bottom only when the user is already near the bottom
// (within 100px).  This lets the user scroll up to read history during
// streaming without being yanked back down.
function scrollToBottomIfNear() {
  const el = messagesRef.value
  if (!el) return
  const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100
  if (nearBottom) {
    el.scrollTop = el.scrollHeight
  }
}

watch(
  () => chat.messages.length,
  () => nextTick(scrollToBottomIfNear)
)
watch(
  () => chat.currentTrace.length,
  () => nextTick(scrollToBottomIfNear)
)
// streaming 过程中 content 在逐字增加，需要实时跟滚
watch(
  () => {
    const last = chat.messages[chat.messages.length - 1]
    return last?.content?.length ?? 0
  },
  () => nextTick(scrollToBottomIfNear)
)

const showScrollButton = ref(false)

function onScroll() {
  const el = messagesRef.value
  if (!el) return
  showScrollButton.value = el.scrollHeight - el.scrollTop - el.clientHeight > 200
}

function scrollToBottom() {
  const el = messagesRef.value
  if (!el) return
  el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
}

onMounted(() => {
  messagesRef.value?.addEventListener('scroll', onScroll, { passive: true })
})
onBeforeUnmount(() => {
  messagesRef.value?.removeEventListener('scroll', onScroll)
})
</script>

<style scoped>
.chat-widget {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem 1.5rem 0.5rem;
}
.messages-list {
  max-width: 768px;
  margin: 0 auto;
}
.scroll-to-bottom {
  position: sticky;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  margin: 0 auto;
  border: 1px solid var(--scroll-to-bottom-border);
  border-radius: 50%;
  background: var(--scroll-to-bottom-bg);
  color: var(--accent-strong);
  cursor: pointer;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  animation: fadeIn 0.2s ease-out;
  transition: border-color 0.2s, transform 0.2s;
  z-index: 10;
}
.scroll-to-bottom:hover {
  border-color: var(--scroll-to-bottom-hover-border);
  transform: translateY(-2px);
}
/* 输入区：粘性底部 + 毛玻璃，与消息区有层次感 */
.input-area {
  padding: 0.75rem 1.5rem 1.25rem;
  background: var(--chat-footer-bg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

@media (max-width: 768px) {
  .messages-area { padding: 0.75rem 1rem 0.5rem; }
  .input-area { padding: 0.5rem 0.75rem 0.75rem; }
}
.privacy-note {
  max-width: 768px;
  margin: 0.35rem auto 0;
  font-size: 0.66rem;
  color: var(--text-3);
  text-align: center;
}

</style>
