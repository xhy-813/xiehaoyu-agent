import { ref, watchEffect } from 'vue'

type Theme = 'dark' | 'light'

const STORAGE_KEY = 'xy-theme'

function readStored(): Theme {
  try {
    const v = localStorage.getItem(STORAGE_KEY)
    if (v === 'light' || v === 'dark') return v
  } catch { /* 隐私模式下 localStorage 可能抛出 */ }
  return 'dark'
}

// 全局单例，确保多个组件共享同一状态
const theme = ref<Theme>(readStored())

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
