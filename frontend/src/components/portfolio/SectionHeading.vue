<template>
  <!-- 修订 3：章节标题视觉隐藏（对齐 brittanychiang v5 —— 章节仅由左栏导航露出）。
       如需恢复可见标题，去掉根元素的 sr-only 类即可 -->
  <h2 class="section-heading sr-only">
    <span class="sh-num">{{ num }}</span>
    <span class="sh-title">{{ title }}</span>
  </h2>
</template>

<script setup lang="ts">
defineProps<{ num: string; title: string }>()
</script>

<style scoped>
.section-heading {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  margin: 0 0 2.25rem;
}
.sh-num {
  font-family: var(--font-mono);
  font-size: 1.5rem;
  font-weight: 500;
  color: var(--accent-strong);
  line-height: 1;
}
.sh-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-bright);
  line-height: 1;
}

/* 修订 3：章节标题视觉隐藏（对齐 brittanychiang v5 —— 章节仅由左栏导航露出）。
   如需恢复可见标题，去掉根元素的 sr-only 类即可 */
.section-heading.sr-only {
  position: absolute;
  width: 1px; height: 1px;
  padding: 0; margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>