import { ref, watchEffect } from 'vue'

type Theme = 'dark' | 'light'

const STORAGE_KEY = 'xy-theme'

function readInitial(): Theme {
  try {
    const v = localStorage.getItem(STORAGE_KEY)
    if (v === 'light' || v === 'dark') return v
  } catch { /* 隐私模式下 localStorage 可能抛出 */ }
  // 08-09 方案 T4-9：无本地偏好时跟随系统主题（仅首次访问生效，之后以本地选择为准）
  if (typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: light)').matches) {
    return 'light'
  }
  return 'dark'
}

// 全局单例，确保多个组件共享同一状态
const theme = ref<Theme>(readInitial())

// 同步到 <html data-theme="...">
watchEffect(() => {
  document.documentElement.setAttribute('data-theme', theme.value)
  try { localStorage.setItem(STORAGE_KEY, theme.value) } catch { /* ignore */ }
})

export function useTheme() {
  function toggle() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
  }
  return { theme, toggle }
}
