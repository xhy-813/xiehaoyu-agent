<template>
  <div class="login-wrapper">
    <!-- Animated gradient background -->
    <div class="login-bg">
      <div class="bg-orb orb-1" />
      <div class="bg-orb orb-2" />
      <div class="bg-orb orb-3" />
    </div>

    <div class="login-content">
      <!-- Brand -->
      <div class="brand-section">
        <div class="brand-icon">
          <AnimatedAvatar :state="welcomeState" :size="80" @animation-end="handleWelcomeEnd" />
        </div>
        <h1 class="brand-title">Xiehaoyu-Agent</h1>
        <p class="brand-subtitle">个人智能体 · 数据问答工作台</p>
      </div>

      <!-- Login card -->
      <div class="card-wrapper">
        <n-card class="login-card" :bordered="true">
          <n-form @submit.prevent="handleLogin" class="login-form">
            <n-form-item>
              <n-input
                v-model:value="code"
                type="password"
                placeholder="请输入访问码"
                size="large"
                :disabled="loading"
                clearable
                show-password-on="click"
                round
                @keydown.enter="handleLogin"
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
            <p class="login-footer">如需访问码，请联系：谢浩宇</p>
          </template>
        </n-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
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
const welcomeState = ref<AvatarState>('welcome')

function handleWelcomeEnd() {
  welcomeState.value = 'idle'
}

async function handleLogin() {
  if (!code.value.trim()) return
  loading.value = true
  try {
    const res = await loginApi(code.value)
    auth.login(res.access_token)
    router.push('/chat')
  } catch (err: any) {
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
  background: #0a0a0f;
  overflow: hidden;
}

/* Animated gradient background */
.login-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
}
.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.15;
  animation: float 20s ease-in-out infinite;
}
.orb-1 {
  width: 500px; height: 500px;
  background: #63e2b7;
  top: -200px; left: -100px;
  animation-delay: 0s;
}
.orb-2 {
  width: 400px; height: 400px;
  background: #6366f1;
  bottom: -150px; right: -100px;
  animation-delay: -7s;
}
.orb-3 {
  width: 300px; height: 300px;
  background: #f59e0b;
  top: 50%; left: 50%;
  animation-delay: -14s;
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
  font-size: 1.8rem;
  font-weight: 800;
  background: linear-gradient(135deg, #63e2b7 0%, #a78bfa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.02em;
}
.brand-subtitle {
  margin: 0.4rem 0 0;
  font-size: 0.88rem;
  color: #777;
  font-weight: 400;
}

/* Card */
.card-wrapper {
  backdrop-filter: blur(12px);
}
.login-card {
  background: rgba(24, 24, 30, 0.85) !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
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
  color: #555;
  margin: 0;
}
</style>