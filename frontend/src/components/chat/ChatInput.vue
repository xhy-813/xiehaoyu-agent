<template>
  <div class="chat-input-wrapper">
    <div class="input-container">
      <n-input
        ref="inputRef"
        v-model:value="text"
        :input-props="{ autofocus: true }"
        type="textarea"
        placeholder="输入问题，Enter 发送，Shift+Enter 换行..."
        :disabled="disabled"
        :autosize="{ minRows: 1, maxRows: 5 }"
        round
        size="large"
        @keydown.enter="handleEnter"
      />
      <div class="input-actions">
        <span class="char-count" v-if="text.length > 0" :class="{ 'char-over': text.length > 300 }">{{ text.length }}{{ text.length > 300 ? '/300' : '' }}</span>
        <n-button
          v-if="streaming"
          circle
          aria-label="停止生成"
          title="停止生成"
          class="send-btn"
          @click="emit('stop')"
        >
          <template #icon>
            <n-icon size="16" color="#0a192f">
              <svg viewBox="0 0 24 24"><path fill="currentColor" d="M6 6h12v12H6z"/></svg>
            </n-icon>
          </template>
        </n-button>
        <n-button
          v-else
          circle
          aria-label="发送"
          title="发送"
          class="send-btn"
          :disabled="!text.trim() || disabled || text.length > 300"
          @click="handleSend"
        >
          <template #icon>
            <n-icon size="18" color="#0a192f">
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
import { ref, onMounted, watch } from 'vue'

const props = defineProps<{ disabled: boolean; streaming?: boolean }>()
const emit = defineEmits<{ send: [question: string]; stop: [] }>()

const text = ref('')
const inputRef = ref<{ focus: () => void } | null>(null)

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

// 页面挂载时自动聚焦
onMounted(() => {
  inputRef.value?.focus()
})

// streaming 结束后重新聚焦，方便连续提问
watch(() => props.streaming, (now) => {
  if (!now) {
    setTimeout(() => inputRef.value?.focus(), 50)
  }
})
</script>

<style scoped>
.chat-input-wrapper {
  max-width: 768px;
  margin: 0 auto;
}
.input-container {
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 28px;
  box-shadow: var(--shadow-pop);
  padding: 0.4rem 0.5rem 0.4rem 1.2rem;
  transition: border-color 0.2s;
}
.input-container:focus-within {
  border-color: var(--accent-strong);
  background: var(--bg-card);
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
.send-btn {
  background: var(--accent-strong) !important;
  transition: background 0.2s ease;
}
.send-btn:hover:not(:disabled) { background: var(--accent-strong-hover) !important; }
.send-btn:disabled { background: #3a4a63 !important; }
.char-count {
  font-size: 0.7rem;
  color: var(--text-3);
  min-width: 20px;
  text-align: center;
  transition: color 0.2s;
}
.char-over {
  color: #ff6b6b;
  font-weight: 600;
}
.input-hint {
  text-align: center;
  font-size: 0.7rem;
  color: var(--text-3);
  margin: 0.4rem 0 0;
}
</style>