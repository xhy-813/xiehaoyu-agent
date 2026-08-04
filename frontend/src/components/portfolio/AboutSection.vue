<template>
  <section id="about" v-reveal>
    <SectionHeading num="01." title="关于" />
    <div class="about-text">
      <!-- intro 为 profile.ts 中的静态可信内容，含 <strong> 高亮 -->
      <p v-for="(p, i) in profile.intro" :key="i" v-html="p" />
    </div>
    <div class="skills-section">
      <p class="skills-title">技术栈 / Tech Stack</p>
      <div class="skills-grid">
        <span v-for="s in skillsFlat" :key="s" class="skill-tag">{{ s }}</span>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import SectionHeading from './SectionHeading.vue'
import { vReveal } from '@/composables/useRevealOnScroll'
import { profile, skillsFlat } from '@/data/profile'
</script>

<style scoped>
.about-text p {
  font-size: 1rem;
  color: var(--text-2);
  line-height: 1.75;
  margin: 0 0 1.25rem;
}
.about-text p:last-child { margin-bottom: 0; }
.about-text :deep(strong) {
  color: var(--text-1);
  font-weight: 600;
}

/* 技术栈平铺（▹ 前缀，等宽字体） */
.skills-section {
  margin-top: 2.25rem;
  padding-top: 1.75rem;
  border-top: 1px solid var(--border-subtle);
}
.skills-title {
  font-family: var(--font-mono);
  font-size: 0.82rem;
  color: var(--accent-strong);
  font-weight: 500;
  margin: 0 0 1rem;
}
.skills-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem 1.75rem;
}
.skill-tag {
  font-family: var(--font-mono);
  font-size: 0.82rem;
  color: var(--text-1);
  position: relative;
  padding-left: 1rem;
}
.skill-tag::before {
  content: '▹';
  position: absolute;
  left: 0;
  color: var(--accent-strong);
}
@media (max-width: 480px) {
  .skills-grid { grid-template-columns: 1fr; }
}
</style>
