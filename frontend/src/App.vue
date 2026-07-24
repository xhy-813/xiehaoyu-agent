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
    fontFamily: '"Inter", "Segoe UI", -apple-system, sans-serif',
    borderRadius: '8px',
    primaryColor: '#63e2b7',
    primaryColorHover: '#7ff0cb',
    primaryColorPressed: '#4dcb9d',
    primaryColorSuppl: '#63e2b7',
  },
  Layout: {
    siderColor: 'rgba(24, 24, 28, 0.95)',
    headerColor: 'rgba(16, 16, 20, 1)',
    footerColor: 'rgba(16, 16, 20, 1)',
  },
  Card: {
    color: 'rgba(255, 255, 255, 0.04)',
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  Input: {
    color: 'rgba(255, 255, 255, 0.06)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderHover: '1px solid rgba(255, 255, 255, 0.2)',
    borderFocus: '1px solid #63e2b7',
  },
  Button: {
    colorPrimary: '#63e2b7',
    colorHoverPrimary: '#7ff0cb',
    colorPressedPrimary: '#4dcb9d',
    textColorPrimary: '#101014',
  },
}
</script>

<style>
@import '@/styles/global.css';
</style>