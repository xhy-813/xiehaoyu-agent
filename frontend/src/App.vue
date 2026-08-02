<template>
  <n-config-provider :theme="darkTheme" :theme-overrides="themeOverrides">
    <n-message-provider>
      <router-view />
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { darkTheme } from 'naive-ui'
import type { GlobalThemeOverrides } from 'naive-ui'

const themeOverrides: GlobalThemeOverrides = {
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
  Tag: {
    // 使用默认深色配色即可
  },
}
</script>

<style>
@import '@/styles/global.css';
</style>
