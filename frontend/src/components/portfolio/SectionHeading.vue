<template>
  <!-- 修订 3：章节标题视觉隐藏（对齐 brittanychiang v5 —— 章节仅由左栏导航露出）。
       移动端单列时恢复可见，提供视觉锚点 -->
  <h2 class="section-heading" aria-label="`${num} ${title}`">
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
  /* 桌面端双列布局时，章节由左栏导航承担，标题视觉隐藏 */
  position: absolute;
  width: 1px; height: 1px;
  padding: 0; margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
.sh-num {
  font-family: var(--font-mono);
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--accent-strong);
  line-height: 1;
}
.sh-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-bright);
  line-height: 1;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

/* 移动端单列布局：左栏导航消失，需要章节标题作视觉锚点 */
@media (max-width: 980px) {
  .section-heading {
    position: static;
    width: auto; height: auto;
    padding: 0; margin: 0 0 1.75rem;
    overflow: visible;
    clip: auto;
    white-space: normal;
    border: none;
  }
}
</style>
