<template>
  <n-config-provider :theme="naiveTheme" :theme-overrides="themeOverrides">
    <n-message-provider>
      <router-view />
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { darkTheme, lightTheme } from 'naive-ui'
import type { GlobalThemeOverrides } from 'naive-ui'
import { useTheme } from '@/composables/useTheme'

const { theme } = useTheme()

const naiveTheme = computed(() => theme.value === 'dark' ? darkTheme : lightTheme)

const darkOverrides: GlobalThemeOverrides = {
  common: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", Inter, sans-serif',
    borderRadius: '10px',
    primaryColor: '#64ffda',
    primaryColorHover: '#7dffe3',
    primaryColorPressed: '#4ee6c3',
    primaryColorSuppl: '#64ffda',
  },
  Card: {
    color: '#112240',
    borderColor: '#233554',
  },
  Input: {
    color: '#0d1b36',
    colorFocus: '#0d1b36',
    border: '1px solid #233554',
    borderHover: '1px solid rgba(100,255,218,0.35)',
    borderFocus: '1px solid #64ffda',
    boxShadowFocus: '0 0 0 2px rgba(100,255,218,0.15)',
  },
  DataTable: {
    thColor: 'rgba(100,255,218,0.04)',
    tdColor: '#112240',
    tdColorStriped: 'rgba(100,255,218,0.02)',
    borderColor: '#233554',
  },
  Tag: {},
}

const lightOverrides: GlobalThemeOverrides = {
  common: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", Inter, sans-serif',
    borderRadius: '10px',
    primaryColor: '#0969da',
    primaryColorHover: '#0550ae',
    primaryColorPressed: '#033d8b',
    primaryColorSuppl: '#0969da',
  },
  Card: {
    color: '#ffffff',
    borderColor: '#d0d7de',
  },
  Input: {
    color: '#f6f8fa',
    colorFocus: '#ffffff',
    border: '1px solid #d0d7de',
    borderHover: '1px solid #0969da',
    borderFocus: '1px solid #0969da',
    boxShadowFocus: '0 0 0 2px rgba(9,105,218,0.15)',
  },
  DataTable: {
    thColor: 'rgba(9,105,218,0.04)',
    tdColor: '#ffffff',
    tdColorStriped: 'rgba(9,105,218,0.02)',
    borderColor: '#d0d7de',
  },
  Tag: {},
}

const themeOverrides = computed<GlobalThemeOverrides>(() =>
  theme.value === 'dark' ? darkOverrides : lightOverrides
)
</script>

<style>
@import '@/styles/global.css';
</style>
