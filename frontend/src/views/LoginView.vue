<template>
  <div class="login-wrapper">
    <!-- Background: single soft orb + data dot grid -->
    <div class="login-bg">
      <div class="bg-orb orb-1" />
    </div>

    <div class="login-content">
      <!-- Brand -->
      <div class="brand-section">
        <div class="brand-icon">
          <AnimatedAvatar :state="welcomeState" :size="80" @animation-end="handleWelcomeEnd" />
        </div>
        <h1 class="brand-title">Xiehaoyu-Agent</h1>
        <p class="brand-subtitle">个人智能体 · <span class="accent">数据问答</span>工作台</p>
      </div>

      <!-- Login card -->
      <div class="card-wrapper">
        <n-card class="login-card" :class="{ shake: loginError }" :bordered="true">
          <n-form @submit.prevent="handleLogin" class="login-form">
            <n-form-item>
              <n-input
                v-model:value="code"
                type="password"
                placeholder="请输入访问码"
                size="large"
                :disabled="loading"
                :status="loginError ? 'error' : undefined"
                clearable
                show-password-on="click"
                round
              >
                <template #prefix>
                  <n-icon size="18"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1s3.1 1.39 3.1 3.1v2z"/></svg></n-icon>
                </template>
              </n-input>
            </n-form-item>
            <n-button
              type="primary"
              block
              size="large"
              round
              :loading="loading"
              @click="handleLogin"
              class="login-btn"
            >
              {{ loading ? '验证中...' : '进入工作台' }}
            </n-button>
          </n-form>
          <template #footer>
            <p class="login-footer">
              如需访问码：
              <a class="contact-link" href="mailto:xiehaoyu12138@163.com">xiehaoyu12138@163.com</a>
              · 微信 <span class="contact-text">xhy18711807395</span>
            </p>
          </template>
        </n-card>
      </div>

      <!-- Capability intro -->
      <div class="caps">
        <div class="cap" v-for="c in caps" :key="c.title">
          <n-icon size="18" color="#0b7a55"><svg viewBox="0 0 24 24"><path fill="currentColor" :d="c.icon" /></svg></n-icon>
          <div class="cap-title">{{ c.title }}</div>
          <div class="cap-desc">{{ c.desc }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useAuthStore } from '@/stores/auth'
import { loginApi } from '@/api/client'
import AnimatedAvatar from '@/components/shared/AnimatedAvatar.vue'
import type { AvatarState } from '@/components/shared/AnimatedAvatar.vue'

const router = useRouter()
const auth = useAuthStore()
const message = useMessage()

const code = ref('')
const loading = ref(false)
const loginError = ref(false)
const welcomeState = ref<AvatarState>('welcome')

watch(code, () => { loginError.value = false })

function handleWelcomeEnd() {
  welcomeState.value = 'idle'
}

const caps = [
  { title: '个人问答', desc: '基于个人知识库，第一人称回答经历与背景', icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z' },
  { title: '数据问答', desc: '自然语言查询 Olist 电商数据集，自动生成 SQL', icon: 'M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z' },
  { title: '图表解读', desc: '自动选择图表类型，输出业务洞察', icon: 'M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99l1.5 1.5z' },
]

async function handleLogin() {
  if (!code.value.trim()) return
  loading.value = true
  try {
    const res = await loginApi(code.value)
    auth.login(res.access_token)
    router.push('/chat')
  } catch (err: any) {
    loginError.value = true
    message.error(err.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 1.5rem;
  background: #ffffff;
  overflow: hidden;
}

/* Background: single soft orb + data dot grid */
.login-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
}
.login-bg::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, rgba(11, 122, 85, 0.08) 1px, transparent 1px);
  background-size: 28px 28px;
  mask-image: radial-gradient(ellipse at center, black 30%, transparent 75%);
  -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 75%);
}
.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.10;
  animation: float 20s ease-in-out infinite;
}
.orb-1 {
  width: 500px; height: 500px;
  background: #63e2b7;
  top: -200px; left: -100px;
}
@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(60px, -40px) scale(1.05); }
  66% { transform: translate(-30px, 30px) scale(0.95); }
}

.login-content {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
}

/* Brand */
.brand-section {
  text-align: center;
  margin-bottom: 2rem;
}
.brand-icon {
  margin-bottom: 0.75rem;
}
.brand-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-1);
  letter-spacing: -0.01em;
}
.brand-subtitle {
  margin: 0.4rem 0 0;
  font-size: 0.88rem;
  color: var(--text-2);
  font-weight: 400;
}
.brand-subtitle .accent {
  color: var(--accent-strong);
  font-weight: 600;
}

/* Card */
.login-card {
  background: #ffffff !important;
  border-color: var(--border) !important;
  box-shadow: var(--shadow-card);
}
.login-card.shake {
  animation: shake 0.3s ease;
}
.login-form {
  padding: 0.5rem 0;
}
.login-btn {
  margin-top: 0.5rem;
  font-weight: 600;
  height: 44px;
}
.login-footer {
  text-align: center;
  font-size: 0.78rem;
  color: var(--text-3);
  margin: 0;
}
.contact-link {
  color: var(--accent-strong);
  text-decoration: none;
}
.contact-link:hover {
  text-decoration: underline;
}
.contact-text {
  color: var(--text-2);
  user-select: all;
}

/* Capability intro */
.caps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
  margin-top: 1.5rem;
}
.cap {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: var(--radius-card);
  padding: 0.9rem 0.8rem;
  text-align: center;
}
.cap-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-1);
  margin-top: 0.4rem;
}
.cap-desc {
  font-size: 0.75rem;
  color: var(--text-3);
  margin-top: 0.25rem;
  line-height: 1.5;
}
@media (max-width: 640px) {
  .caps { grid-template-columns: 1fr; }
}
</style>
