<template>
  <footer class="site-footer" v-reveal>
    <p>
      由 <a :href="`mailto:${profile.email}`">谢浩宇</a> 设计构建 ·
      Vue 3 · FastAPI · LangGraph · DeepSeek · ChromaDB · &copy; 2026
    </p>
  </footer>
</template>

<script setup lang="ts">
import { vReveal } from '@/composables/useRevealOnScroll'
import { profile } from '@/data/profile'
</script>

<style scoped>
.site-footer {
  text-align: center;
  padding-top: 1.9rem;
  border-top: 1px solid rgba(136, 146, 176, 0.1);
}
.site-footer p {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--text-2);
  margin: 0;
}
.site-footer a {
  color: var(--accent-strong);
  text-decoration: none;
}
.site-footer a:hover { text-decoration: underline; }
</style>