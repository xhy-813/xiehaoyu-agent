<template>
  <n-layout has-sider class="chat-layout">
    <!-- Sidebar -->
    <ChatSidebar
      v-if="!isMobile || showSidebar"
      :class="{ 'mobile-overlay': isMobile }"
      @close="showSidebar = false"
    />

    <!-- Main chat area (full width, no right panel) -->
    <n-layout-content class="chat-main-area">
      <!-- Mobile header -->
      <div v-if="isMobile" class="mobile-bar">
        <n-button text size="small" @click="showSidebar = !showSidebar">
          <template #icon>
            <n-icon size="18"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg></n-icon>
          </template>
        </n-button>
        <span class="mobile-title">Xiehaoyu-Agent</span>
        <div />
      </div>

      <ChatMain />
    </n-layout-content>
  </n-layout>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import ChatSidebar from '@/components/chat/ChatSidebar.vue'
import ChatMain from '@/components/chat/ChatMain.vue'

const showSidebar = ref(false)
const isMobile = ref(false)

function checkMobile() {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})
onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
.chat-layout {
  height: 100vh;
}
.chat-main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.mobile-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(16, 16, 20, 0.95);
}
.mobile-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: #e0e0e0;
}

.mobile-overlay {
  position: fixed !important;
  top: 0; left: 0; bottom: 0;
  z-index: 100;
  width: 280px !important;
  box-shadow: 4px 0 16px rgba(0, 0, 0, 0.5);
}
</style>