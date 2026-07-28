<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-message-provider>
      <router-view />
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import type { GlobalThemeOverrides } from 'naive-ui'

const themeOverrides: GlobalThemeOverrides = {
  common: {
    fontFamily: '"Segoe UI", -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif',
    borderRadius: '10px',
    primaryColor: '#0b7a55',
    primaryColorHover: '#0d9463',
    primaryColorPressed: '#096a48',
    primaryColorSuppl: '#0b7a55',
    textColor1: '#1f2328',
    textColor2: '#5c6370',
    textColor3: '#6b7280',
    borderColor: 'rgba(0,0,0,0.08)',
  },
  Layout: {
    siderColor: '#f9f9f9',
    color: '#ffffff',
  },
  Card: {
    color: '#ffffff',
    borderColor: 'rgba(0,0,0,0.08)',
  },
  Input: {
    color: '#ffffff',
    colorFocus: '#ffffff',
    border: '1px solid rgba(0,0,0,0.12)',
    borderHover: '1px solid rgba(0,0,0,0.2)',
    borderFocus: '1px solid #0b7a55',
    boxShadowFocus: '0 0 0 2px rgba(11,122,85,0.15)',
  },
  Button: {
    colorPrimary: '#1f2328',
    colorHoverPrimary: '#3a4048',
    colorPressedPrimary: '#111418',
    textColorPrimary: '#ffffff',
    textColorHoverPrimary: '#ffffff',
    textColorPressedPrimary: '#ffffff',
  },
  DataTable: {
    thColor: 'rgba(0,0,0,0.02)',
    thTextColor: '#5c6370',
    borderColor: 'rgba(0,0,0,0.06)',
  },
}
</script>

<style>
@import '@/styles/global.css';
</style>