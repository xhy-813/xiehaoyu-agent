<template>
  <section id="ai-chat" v-reveal>
    <div class="ai-banner">
      <div class="ai-info">
        <span class="ai-badge">智能对话入口</span>
        <h3 class="ai-title">AI 问答助手</h3>
        <p class="ai-desc">
          基于大语言模型的智能问答系统：检索个人知识库回答「我是谁」，
          也能用自然语言查询 Olist 电商数据（Text2SQL → 自动可视化 → 结果解读）。
          无需登录，点击即可进入对话界面。
        </p>
      </div>
      <button class="ai-btn" @click="goChat">
        进入 AI 问答
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { vReveal } from '@/composables/useRevealOnScroll'

const router = useRouter()

function goChat() {
  router.push('/chat')
}
</script>

<style scoped>
.ai-banner {
  background: linear-gradient(135deg, rgba(100, 255, 218, 0.07) 0%, rgba(100, 255, 218, 0.02) 50%, transparent 100%);
  border: 1px solid rgba(100, 255, 218, 0.16);
  border-radius: 14px;
  padding: 46px 42px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 36px;
  position: relative;
  overflow: hidden;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}
.ai-banner:hover {
  border-color: rgba(100, 255, 218, 0.3);
  box-shadow: 0 0 40px rgba(100, 255, 218, 0.06);
}
/* 浮动光斑 */
.ai-banner::before {
  content: '';
  position: absolute;
  top: -60%;
  right: -15%;
  width: 420px;
  height: 420px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(100, 255, 218, 0.07) 0%, transparent 70%);
  pointer-events: none;
  animation: float-blob 8s ease-in-out infinite;
}
.ai-info { position: relative; z-index: 1; }
.ai-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--accent-strong);
  background: rgba(100, 255, 218, 0.1);
  padding: 5px 13px;
  border-radius: 20px;
  margin-bottom: 16px;
  font-weight: 500;
  border: 1px solid rgba(100, 255, 218, 0.15);
}
.ai-badge::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent-strong);
  animation: pulse-glow 2s infinite;
}
.ai-title {
  font-size: 1.7rem;
  font-weight: 700;
  color: var(--text-bright);
  margin: 0 0 0.5rem;
}
.ai-desc {
  font-size: 0.95rem;
  color: var(--text-2);
  line-height: 1.6;
  max-width: 450px;
  margin: 0;
}
.ai-btn {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 16px 34px;
  background: var(--accent-strong);
  color: var(--bg-base);
  font-size: 0.95rem;
  font-weight: 700;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s ease;
}
.ai-btn:hover {
  transform: translateY(-3px) scale(1.03);
  box-shadow: 0 10px 32px rgba(100, 255, 218, 0.35);
}
.ai-btn svg {
  width: 18px;
  height: 18px;
  transition: transform 0.3s ease;
}
.ai-btn:hover svg { transform: translateX(4px); }

@media (max-width: 980px) {
  .ai-banner { flex-direction: column; text-align: center; padding: 36px 28px; }
  .ai-desc { max-width: 100%; }
}
</style>