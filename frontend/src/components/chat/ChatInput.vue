<template>
  <div class="chat-input-wrapper">
    <div class="input-container">
      <n-input
        ref="inputRef"
        v-model:value="text"
        type="textarea"
        placeholder="输入问题，Enter 发送，Shift+Enter 换行..."
        :disabled="disabled"
        :autosize="{ minRows: 1, maxRows: 5 }"
        round
        size="large"
        @keydown.enter="handleEnter"
      />
      <div class="input-actions">
        <span class="char-count" v-if="text.length > 0">{{ text.length }}</span>
        <n-button
          type="primary"
          :disabled="!text.trim() || disabled"
          :loading="disabled"
          circle
          @click="handleSend"
        >
          <template #icon>
            <n-icon size="18">
              <svg viewBox="0 0 24 24"><path fill="currentColor" d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
            </n-icon>
          </template>
        </n-button>
      </div>
    </div>
    <p class="input-hint" v-if="!disabled">Enter 发送 · Shift+Enter 换行</p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{ disabled: boolean }>()
const emit = defineEmits<{ send: [question: string] }>()

const text = ref('')

function handleSend() {
  const q = text.value.trim()
  if (!q) return
  emit('send', q)
  text.value = ''
}

function handleEnter(e: KeyboardEvent) {
  if (e.shiftKey) return
  e.preventDefault()
  handleSend()
}
</script>

<style scoped>
.chat-input-wrapper {
  max-width: 760px;
  margin: 0 auto;
}
.input-container {
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 0.4rem 0.5rem 0.4rem 1.2rem;
  transition: border-color 0.2s;
}
.input-container:focus-within {
  border-color: rgba(99, 226, 183, 0.4);
  background: rgba(255, 255, 255, 0.05);
}
.input-container :deep(.n-input) {
  flex: 1;
  --n-border: none !important;
  --n-border-hover: none !important;
  --n-border-focus: none !important;
  --n-box-shadow-focus: none !important;
}
.input-actions {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding-bottom: 2px;
}
.char-count {
  font-size: 0.7rem;
  color: #555;
  min-width: 20px;
  text-align: center;
}
.input-hint {
  text-align: center;
  font-size: 0.7rem;
  color: #555;
  margin: 0.4rem 0 0;
}
</style>