<template>
  <div class="welcome">
    <div class="welcome-icon">
      <AnimatedAvatar :state="welcomeState" :size="80" @animation-end="handleWelcomeEnd" />
    </div>
    <h2 class="welcome-title">你好，我是 Xiehaoyu-Agent</h2>
    <p class="welcome-desc">
      你可以向我提问个人经历、技术栈，或者直接发起数据分析请求。
    </p>

    <div class="quick-cards">
      <div
        v-for="group in groups"
        :key="group.name"
        class="quick-card"
        @click="handleQuick(group.questions[0])"
      >
        <div class="qc-icon" :style="{ background: group.bg }">
          <n-icon size="22" :color="group.color">
            <svg viewBox="0 0 24 24"><path fill="currentColor" :d="group.icon" /></svg>
          </n-icon>
        </div>
        <div class="qc-info">
          <div class="qc-name">{{ group.name }}</div>
          <div class="qc-hint">{{ group.hint }}</div>
        </div>
        <n-icon size="16" color="#555" class="qc-arrow">
          <svg viewBox="0 0 24 24"><path fill="currentColor" d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6z"/></svg>
        </n-icon>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '@/stores/chat'
import AnimatedAvatar from '@/components/shared/AnimatedAvatar.vue'
import type { AvatarState } from '@/components/shared/AnimatedAvatar.vue'

const chat = useChatStore()

const welcomeState = ref<AvatarState>('welcome')

function handleWelcomeEnd() {
  welcomeState.value = 'idle'
}

function handleQuick(q: string) {
  if (chat.isStreaming) return
  chat.sendMessage(q)
}

const groups = [
  {
    name: '自我介绍',
    hint: '了解我的背景和经历',
    questions: ['介绍一下你自己'],
    color: '#63e2b7',
    bg: 'rgba(99, 226, 183, 0.12)',
    icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z',
  },
  {
    name: '数据分析',
    hint: '查询 Olist 电商数据',
    questions: ['2018 年每月订单数，帮我画个图'],
    color: '#818cf8',
    bg: 'rgba(129, 140, 248, 0.12)',
    icon: 'M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z',
  },
  {
    name: '项目经历',
    hint: '了解我做过什么项目',
    questions: ['你做过哪些和数据相关的项目？'],
    color: '#f59e0b',
    bg: 'rgba(245, 158, 11, 0.12)',
    icon: 'M20 6h-8l-2-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V6h5.17l2 2H20v10z',
  },
]
</script>

<style scoped>
.welcome {
  max-width: 560px;
  margin: 3rem auto;
  padding: 0 1rem;
}
.welcome-icon {
  display: inline-block;
  margin-bottom: 1.25rem;
}
.welcome-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #e8e8e8;
  margin: 0 0 0.5rem;
  letter-spacing: -0.01em;
}
.welcome-desc {
  color: #777;
  font-size: 0.92rem;
  margin: 0 0 2rem;
  line-height: 1.5;
}

/* Quick cards */
.quick-cards {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.quick-card {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  padding: 0.85rem 1rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.quick-card:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.12);
  transform: translateX(4px);
}
.qc-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.qc-info {
  flex: 1;
  text-align: left;
}
.qc-name {
  font-size: 0.92rem;
  font-weight: 600;
  color: #e0e0e0;
}
.qc-hint {
  font-size: 0.78rem;
  color: #666;
  margin-top: 0.15rem;
}
.qc-arrow {
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.2s;
}
.quick-card:hover .qc-arrow {
  opacity: 1;
}
</style>