<template>
  <div class="msg-bubble" :class="{ 'msg-bubble-error': isError }">
    <div
      class="msg-content"
      :class="{ 'streaming-cursor': isStreaming || cursorFading, 'fade-out': cursorFading }"
      v-html="renderedContent"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { renderMarkdown } from '@/utils/markdown'

const props = defineProps<{
  content: string
  isError?: boolean
  isStreaming?: boolean
}>()

const renderedContent = computed(() => renderMarkdown(props.content))

const cursorFading = ref(false)

watch(() => props.isStreaming, (now, prev) => {
  if (prev && !now) {
    cursorFading.value = true
    setTimeout(() => { cursorFading.value = false }, 300)
  }
})
</script>

<style scoped>
.msg-bubble {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  overflow-wrap: break-word;
}
/* 错误气泡三色由 global.css 按主题定义（08-09 方案 T4-6） */
.msg-bubble-error {
  background: var(--error-bg);
  border: 1px solid var(--error-border);
  border-radius: 12px;
  padding: 0.6rem 0.9rem;
}
.msg-bubble-error .msg-content { color: var(--error-text); }
.msg-content {
  font-size: 0.875rem;
  line-height: 1.7;
  color: var(--text-1);
  word-break: break-word;
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
</style>