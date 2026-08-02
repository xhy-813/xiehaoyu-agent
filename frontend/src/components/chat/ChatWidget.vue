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
        />
      </div>
    </div>

    <!-- Input area -->
    <div class="input-area">
      <ChatInput
        :disabled="chat.isStreaming"
        :streaming="chat.isStreaming"
        @send="handleSend"
        @stop="chat.stopStreaming"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { watch, nextTick, ref } from 'vue'
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
  padding: 1.25rem 1.5rem;
}
.messages-list {
  max-width: 768px;
  margin: 0 auto;
}
.input-area {
  padding: 0 1.5rem 1.25rem;
}

@media (max-width: 768px) {
  .messages-area { padding: 0.75rem 1rem; }
  .input-area { padding: 0 0.75rem 0.75rem; }
}
</style>