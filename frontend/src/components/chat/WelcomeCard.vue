<template>
  <div class="welcome">
    <div class="welcome-icon">
      <AnimatedAvatar :state="welcomeState" :size="96" @animation-end="handleWelcomeEnd" />
    </div>
    <h2 class="welcome-title">你好，我是 Xiehaoyu-Agent</h2>
    <p class="welcome-desc">可以问我个人经历与技术栈，或直接发起数据分析请求。</p>

    <div class="chips" :class="{ disabled: chat.isStreaming }">
      <button
        v-for="q in WELCOME_QUESTIONS"
        :key="q.question"
        class="chip"
        :disabled="chat.isStreaming"
        @click="handleQuick(q.question)"
      >
        {{ q.question }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '@/stores/chat'
import AnimatedAvatar from '@/components/shared/AnimatedAvatar.vue'
import type { AvatarState } from '@/components/shared/AnimatedAvatar.vue'
import { WELCOME_QUESTIONS } from '@/utils/quick-questions'

const chat = useChatStore()
const welcomeState = ref<AvatarState>('welcome')

function handleWelcomeEnd() {
  welcomeState.value = 'idle'
}

function handleQuick(q: string) {
  if (chat.isStreaming) return
  chat.sendMessage(q)
}
</script>

<style scoped>
.welcome {
  max-width: 560px;
  margin: 4rem auto 0;
  padding: 0 1rem;
  text-align: center;
}
.welcome-icon { margin-bottom: 1.25rem; }
.welcome-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-1);
  margin: 0 0 0.5rem;
  letter-spacing: -0.01em;
}
.welcome-desc {
  color: var(--text-2);
  font-size: 0.875rem;
  margin: 0 0 2rem;
}
.chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.5rem;
}
.chips.disabled .chip {
  opacity: 0.45;
  cursor: not-allowed;
}
.chip {
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
  background: #fff;
  color: var(--text-1);
  font-size: 0.8125rem;
  padding: 0.45rem 0.95rem;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease;
}
.chip:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.03);
  border-color: var(--border-strong);
}
</style>
