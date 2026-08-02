<template>
  <aside class="site-sidebar">
    <div class="ss-top">
      <div class="ss-hero">
        <h1 class="ss-name">{{ profile.name }}</h1>
        <p class="ss-role">{{ profile.role }}</p>
        <p class="ss-tagline">{{ profile.tagline }}</p>
      </div>

      <nav class="ss-nav" aria-label="页面区块导航">
        <a
          v-for="l in links"
          :key="l.id"
          :href="`#${l.id}`"
          class="ss-link"
          :class="{ active: activeId === l.id, 'ai-entry': l.id === 'ai-chat' }"
        >
          <span class="ss-line" aria-hidden="true" />
          <span class="ss-label">
            {{ l.label }}<span v-if="l.id === 'ai-chat'" class="ai-dot" aria-hidden="true" />
          </span>
        </a>
      </nav>
    </div>

    <ul class="ss-socials">
      <li>
        <a :href="profile.repo" target="_blank" rel="noopener" aria-label="代码仓库" title="代码仓库">
          <svg viewBox="0 0 24 24" width="19" height="19"><path fill="currentColor" d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.55v-2.17c-3.2.7-3.87-1.36-3.87-1.36-.52-1.33-1.28-1.68-1.28-1.68-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.19 1.76 1.19 1.03 1.75 2.69 1.25 3.34.95.1-.74.4-1.25.72-1.53-2.55-.29-5.23-1.28-5.23-5.68 0-1.26.45-2.28 1.19-3.09-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.17 1.18a11.1 11.1 0 0 1 5.78 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.83 1.19 3.09 0 4.41-2.69 5.38-5.25 5.66.41.35.77 1.05.77 2.12v3.15c0 .3.21.67.8.55A11.51 11.51 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5z"/></svg>
        </a>
      </li>
      <li>
        <a :href="`mailto:${profile.email}`" aria-label="邮箱" :title="profile.email">
          <svg viewBox="0 0 24 24" width="19" height="19"><path fill="currentColor" d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4-8 5-8-5V6l8 5 8-5v2z"/></svg>
        </a>
      </li>
      <li>
        <button class="ss-wechat" aria-label="复制微信号" :title="`微信：${profile.wechat}（点击复制）`" @click="copyWechat">
          <svg viewBox="0 0 24 24" width="19" height="19"><path fill="currentColor" d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-9 9H7V9h4v2zm6 0h-4V9h4v2z"/></svg>
        </button>
      </li>
    </ul>
  </aside>
</template>

<script setup lang="ts">
import { useMessage } from 'naive-ui'
import { profile } from '@/data/profile'
import { useScrollSpy } from '@/composables/useScrollSpy'

const links = [
  { id: 'about', label: '关于' },
  { id: 'experience', label: '经历' },
  { id: 'projects', label: '项目' },
  { id: 'ai-chat', label: 'AI 问答' },
]

const activeId = useScrollSpy(links.map((l) => l.id))

const message = useMessage()

async function copyWechat() {
  try {
    await navigator.clipboard.writeText(profile.wechat)
    message.success('微信号已复制')
  } catch {
    message.warning(`复制失败，请手动添加：${profile.wechat}`)
  }
}
</script>

<style scoped>
/* 桌面端：fixed 左栏（右列用 margin-left 让位，见 PortfolioView） */
.site-sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 42%;
  max-width: 480px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 10vh 40px 6vh 10vw;
  z-index: 50;
  overflow-y: auto;
  scrollbar-width: none;
}
.site-sidebar::-webkit-scrollbar { display: none; }

.ss-hero {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 40px;
}
.ss-name {
  font-size: clamp(32px, 4.5vw, 56px);
  font-weight: 700;
  color: var(--text-bright);
  letter-spacing: -0.02em;
  line-height: 1.1;
  margin: 0;
}
.ss-role {
  font-size: clamp(16px, 2vw, 22px);
  font-weight: 500;
  color: var(--text-2);
  margin: -4px 0 0;
}
.ss-tagline {
  font-size: clamp(14px, 1.6vw, 17px);
  color: var(--text-2);
  line-height: 1.65;
  max-width: 360px;
  margin: 0;
  padding-top: 12px;
  border-top: 1px solid rgba(136, 146, 176, 0.15);
}

/* 横线指示器导航 */
.ss-nav {
  display: flex;
  flex-direction: column;
}
.ss-link {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 13px 0;
  text-decoration: none;
}
.ss-line {
  width: 44px;
  height: 1px;
  background: var(--text-2);
  flex-shrink: 0;
  transition: width 0.3s ease, background 0.3s ease;
}
.ss-label {
  font-family: var(--font-mono);
  font-size: 12.5px;
  font-weight: 500;
  color: var(--text-2);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  white-space: nowrap;
  transition: color 0.25s ease, transform 0.25s ease;
}
.ss-link:hover .ss-line,
.ss-link.active .ss-line {
  width: 70px;
  background: var(--text-bright);
}
.ss-link:hover .ss-label,
.ss-link.active .ss-label {
  color: var(--accent-strong);
  transform: translateX(4px);
}
/* AI 问答入口项：常驻高亮 + 脉冲圆点 */
.ss-link.ai-entry .ss-label {
  color: var(--accent-strong);
  font-weight: 700;
}
.ss-link.ai-entry .ss-line {
  width: 60px;
  background: var(--text-bright);
}
.ai-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent-strong);
  margin-left: 8px;
  vertical-align: middle;
  animation: pulse-glow 2s infinite;
}

/* 社交图标 */
.ss-socials {
  display: flex;
  align-items: center;
  gap: 20px;
  list-style: none;
  margin: 0;
  padding: 24px 0 0;
}
.ss-socials a,
.ss-wechat {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-2);
  background: none;
  border: 1px solid transparent;
  padding: 0;
  cursor: pointer;
  transition: color 0.3s ease, border-color 0.3s ease, transform 0.3s ease, box-shadow 0.3s ease;
}
.ss-socials a:hover,
.ss-wechat:hover {
  color: var(--accent-strong);
  border-color: rgba(100, 255, 218, 0.25);
  transform: translateY(-3px);
  box-shadow: 0 4px 14px rgba(100, 255, 218, 0.12);
}

/* ≤1200px：左栏收窄 */
@media (max-width: 1200px) {
  .site-sidebar { width: 38%; padding-left: 6vw; }
}

/* ≤980px：顶部静态身份块 + 横向导航行 */
@media (max-width: 980px) {
  .site-sidebar {
    position: relative;
    width: 100%;
    max-width: none;
    padding: 8vh 6vw 4vh;
    border-bottom: 1px solid rgba(136, 146, 176, 0.1);
    overflow: visible;
  }
  .ss-hero { margin-bottom: 32px; }
  .ss-tagline { max-width: 100%; }
  .ss-nav { flex-direction: row; flex-wrap: wrap; gap: 0 8px; }
  .ss-link { padding: 10px 0; }
  .ss-line { width: 32px; }
  .ss-socials { justify-content: center; padding-top: 20px; }
}
@media (max-width: 480px) {
  .site-sidebar { padding: 6vh 5vw; }
}
</style>