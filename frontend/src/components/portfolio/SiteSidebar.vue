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
        <a :href="profile.gitee" target="_blank" rel="noopener" aria-label="Gitee 主页" title="Gitee 主页">
          <svg viewBox="0 0 24 24" width="19" height="19"><path fill="currentColor" d="M11.984 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.016 0zm6.09 5.333c.328 0 .593.266.592.593v1.482a.594.594 0 0 1-.593.592H9.777c-.982 0-1.778.796-1.778 1.778v5.63c0 .327.266.592.593.592h5.63c.982 0 1.778-.796 1.778-1.778v-.296a.593.593 0 0 0-.592-.593h-4.15a.592.592 0 0 1-.592-.592v-1.482a.593.593 0 0 1 .593-.592h6.815c.327 0 .593.265.593.592v3.408a4 4 0 0 1-4 4H5.926a.593.593 0 0 1-.593-.593V9.778a4.444 4.444 0 0 1 4.445-4.444h8.296Z"/></svg>
        </a>
      </li>
      <li>
        <a :href="profile.github" target="_blank" rel="noopener" aria-label="GitHub 主页" title="GitHub 主页">
          <svg viewBox="0 0 24 24" width="19" height="19"><path fill="currentColor" d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.55v-2.17c-3.2.7-3.87-1.36-3.87-1.36-.52-1.33-1.28-1.68-1.28-1.68-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.19 1.76 1.19 1.03 1.75 2.69 1.25 3.34.95.1-.74.4-1.25.72-1.53-2.55-.29-5.23-1.28-5.23-5.68 0-1.26.45-2.28 1.19-3.09-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.17 1.18a11.1 11.1 0 0 1 5.78 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.83 1.19 3.09 0 4.41-2.69 5.38-5.25 5.66.41.35.77 1.05.77 2.12v3.15c0 .3.21.67.8.55A11.51 11.51 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5z"/></svg>
        </a>
      </li>
      <li>
        <a :href="profile.csdn" target="_blank" rel="noopener" aria-label="CSDN 博客" title="CSDN 博客">
          <svg viewBox="0 0 24 24" width="19" height="19"><path fill="currentColor" d="M4.693 13.638c-.497.568-1.363.63-1.712.63-.648 0-1.144-.164-1.474-.488-.313-.307-.478-.76-.489-1.346-.025-1.358.744-2.762 2.074-2.762.635 0 1.124.455 1.311.644a.337.337 0 0 0 .282.099.38.38 0 0 0 .241-.159c.068-.087.135-.237.138-.401s-.057-.344-.243-.49a2.642 2.642 0 0 0-1.668-.591c-.819 0-1.627.376-2.218 1.033-.621.691-.953 1.63-.935 2.646.015.815.282 1.5.773 1.982.528.518 1.3.791 2.235.791 1.097 0 1.776-.325 2.154-.597a.584.584 0 0 0 .24-.456.702.702 0 0 0-.208-.497c-.23-.248-.448-.101-.503-.037ZM9.663 11.488a7.471 7.471 0 0 0-.698-.248c-.157-.048-.309-.091-.45-.131-.922-.26-1.027-.5-1.017-.68.022-.363.515-.853 1.352-.792.607.045 1.015.509 1.205.781.149.214.371.135.434.095a.602.602 0 0 0 .309-.514.626.626 0 0 0-.209-.488 2.654 2.654 0 0 0-3.347-.273c-.456.323-.744.772-.77 1.202-.064 1.061 1.015 1.366 1.803 1.588.214.061.429.127.667.202 1.14.357 1.173.717 1.092 1.267-.082.556-.696.834-1.685.761-1.029-.076-1.464-.61-1.612-.901-.05-.098-.205-.248-.413-.156-.514.229-.473.731-.26.993.339.416 1.15 1.035 2.667 1.035 1.734 0 2.255-.875 2.378-1.64.092-.572-.022-1.028-.348-1.396-.236-.267-.592-.495-1.101-.706ZM16.44 9.323c-.598-.431-1.393-.61-2.36-.532-.712.058-1.274.243-1.335.263l-.006.002a.437.437 0 0 0-.297.379l-.47 5.201a.337.337 0 0 0 .247.35l.072.02.066.018.086.021a7.914 7.914 0 0 0 1.64.183c.972 0 1.765-.23 2.36-.684.764-.583 1.141-1.5 1.118-2.725-.021-1.135-.398-1.974-1.121-2.495Zm-.662 4.461c-.836.639-2.09.562-2.677.481a.128.128 0 0 1-.109-.137l.397-4.248a.113.113 0 0 1 .086-.1c.999-.241 1.777-.168 2.312.218.189.137.348.331.471.568.176.339.277.765.286 1.234.017.916-.24 1.583-.765 1.984ZM23.967 10.41a1.92 1.92 0 0 0-.432-.919c-.399-.465-1.029-.689-1.848-.689-.734 0-1.372.228-1.947.799.007-.086.019-.159.018-.223s-.017-.116-.066-.163c-.048-.045-.077-.067-.127-.077-.05-.01-.122-.008-.256-.006a.587.587 0 0 0-.589.54s-.325 3.874-.428 5.165a.308.308 0 0 0 .073.228.36.36 0 0 0 .26.131h.387a.224.224 0 0 0 .226-.205l.273-2.929.014-.147a1.902 1.902 0 0 1 .082-.412c.014-.045.03-.092.047-.14.245-.694.803-1.72 1.971-1.694.84.018 1.449.455 1.385 1.114-.101 1.034-.266 3.1-.358 4.14-.019.209.182.273.252.273h.304a.442.442 0 0 0 .444-.404s.185-2.127.294-3.352l.048-.532a1.959 1.959 0 0 0-.026-.5Z"/></svg>
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
      <!-- 主题切换按钮 -->
      <li>
        <button
          class="ss-theme-btn"
          :aria-label="theme === 'dark' ? '切换到浅色模式' : '切换到深色模式'"
          :title="theme === 'dark' ? '切换到浅色模式' : '切换到深色模式'"
          @click="toggleTheme"
        >
          <!-- 深色模式显示太阳（点击切换到浅色） -->
          <svg v-if="theme === 'dark'" viewBox="0 0 24 24" width="19" height="19">
            <path fill="currentColor" d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1zM5.99 4.58a.996.996 0 0 0-1.41 0 .996.996 0 0 0 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0s.39-1.03 0-1.41L5.99 4.58zm12.37 12.37a.996.996 0 0 0-1.41 0 .996.996 0 0 0 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0a.996.996 0 0 0 0-1.41l-1.06-1.06zm1.06-12.37-1.06 1.06a.996.996 0 0 0 0 1.41c.39.39 1.03.39 1.41 0l1.06-1.06a.996.996 0 0 0 0-1.41.996.996 0 0 0-1.41 0zM7.05 18.36l-1.06 1.06a.996.996 0 0 0 0 1.41c.39.39 1.03.39 1.41 0l1.06-1.06a.996.996 0 0 0 0-1.41.996.996 0 0 0-1.41 0z"/>
          </svg>
          <!-- 浅色模式显示月亮（点击切换到深色） -->
          <svg v-else viewBox="0 0 24 24" width="19" height="19">
            <path fill="currentColor" d="M12 3a9 9 0 1 0 9 9c0-.46-.04-.92-.1-1.36a5.389 5.389 0 0 1-4.4 2.26 5.403 5.403 0 0 1-3.14-9.8c-.44-.06-.9-.1-1.36-.1z"/>
          </svg>
        </button>
      </li>
    </ul>
  </aside>
</template>

<script setup lang="ts">
import { useMessage } from 'naive-ui'
import { profile } from '@/data/profile'
import { useScrollSpy } from '@/composables/useScrollSpy'
import { useTheme } from '@/composables/useTheme'

const links = [
  { id: 'about', label: '关于' },
  { id: 'experience', label: '经历' },
  { id: 'projects', label: '项目' },
  { id: 'ai-chat', label: 'AI 问答' },
]

const activeId = useScrollSpy(links.map((l) => l.id))

const message = useMessage()
const { theme, toggle: toggleTheme } = useTheme()

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
  /* clamp 防止超宽屏时左边距失控；右侧固定 40px 与右列内容呼应 */
  padding: 10vh 40px 6vh clamp(2rem, 10vw, 80px);
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
  border-top: 1px solid var(--border-subtle);
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
.ss-wechat,
.ss-theme-btn {
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
.ss-wechat:hover,
.ss-theme-btn:hover {
  color: var(--accent-strong);
  border-color: rgba(100, 255, 218, 0.25);
  transform: translateY(-3px);
  box-shadow: 0 4px 14px rgba(100, 255, 218, 0.12);
}
/* 浅色模式下 hover 颜色换成蓝色系 */
[data-theme="light"] .ss-socials a:hover,
[data-theme="light"] .ss-wechat:hover,
[data-theme="light"] .ss-theme-btn:hover {
  border-color: rgba(9, 105, 218, 0.25);
  box-shadow: 0 4px 14px rgba(9, 105, 218, 0.12);
}

/* ≤1200px：左栏收窄 */
@media (max-width: 1200px) {
  .site-sidebar { width: 38%; padding-left: clamp(1.5rem, 6vw, 56px); }
}

/* ≤980px：顶部静态身份块 + 横向导航行 */
@media (max-width: 980px) {
  .site-sidebar {
    position: relative;
    width: 100%;
    max-width: none;
    padding: 8vh 6vw 4vh;
    border-bottom: 1px solid var(--border-subtle);
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
