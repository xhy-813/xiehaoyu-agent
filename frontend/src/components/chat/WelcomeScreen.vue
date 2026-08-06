<template>
  <div class="welcome-screen">
    <div class="ws-glow" />
    <div class="ws-content">
      <AnimatedAvatar :state="avatarState" :size="88" />
      <h2 class="ws-title">你好，我是谢浩宇的数字分身</h2>
      <p class="ws-subtitle">
        可以问我个人经历与技术栈，或让我查数据、画图表
      </p>
      <div class="ws-chips">
        <button
          v-for="(q, i) in questions"
          :key="q.question"
          class="ws-chip"
          :style="{ animationDelay: `${0.08 * i}s` }"
          :disabled="disabled"
          @click="$emit('ask', q.question)"
        >
          {{ q.question }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import AnimatedAvatar from '@/components/shared/AnimatedAvatar.vue'
import { WELCOME_QUESTIONS } from '@/utils/quick-questions'
import type { AvatarState } from '@/components/shared/AnimatedAvatar.vue'

const props = withDefaults(defineProps<{
  avatarState?: AvatarState
  disabled?: boolean
}>(), {
  avatarState: 'idle',
  disabled: false,
})

defineEmits<{ ask: [question: string] }>()

const questions = WELCOME_QUESTIONS
</script>

<style scoped>
.welcome-screen {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}
.ws-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: radial-gradient(
    circle,
    rgba(100, 255, 218, 0.08) 0%,
    rgba(100, 255, 218, 0.03) 40%,
    transparent 70%
  );
  pointer-events: none;
}
.ws-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 1rem;
  gap: 0.75rem;
}
.ws-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-bright);
  margin: 0;
  letter-spacing: 0.02em;
}
.ws-subtitle {
  font-size: 0.9rem;
  color: var(--text-2);
  line-height: 1.6;
  max-width: 420px;
  margin: 0;
}
.ws-chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.5rem;
  max-width: 520px;
  margin-top: 0.5rem;
}
.ws-chip {
  font-family: var(--font-mono);
  border: 1px solid var(--chip-border);
  border-radius: var(--radius-pill);
  background: var(--chip-bg);
  color: var(--accent-strong);
  font-size: 0.75rem;
  padding: 0.45rem 0.95rem;
  cursor: pointer;
  opacity: 0;
  animation: ws-fadeInUp 0.4s ease-out forwards;
  transition: color 0.2s, border-color 0.2s, background 0.2s, transform 0.2s, box-shadow 0.2s;
}
.ws-chip:hover:not(:disabled) {
  border-color: var(--chip-border-hover);
  background: var(--chip-bg-hover);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(100, 255, 218, 0.1);
}
.ws-chip:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

@keyframes ws-fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>