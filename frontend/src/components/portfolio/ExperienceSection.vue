<template>
  <section id="experience" v-reveal>
    <SectionHeading num="02." title="经历" />
    <ol class="exp-list stagger">
      <li v-for="e in experiences" :key="e.company" class="exp-item" v-reveal>
        <span class="exp-year">{{ e.period }}</span>
        <div class="exp-detail">
          <div class="exp-role-line">
            <span class="exp-role">{{ e.role }} ·</span>
            <span class="exp-company">{{ e.company }}</span>
          </div>
          <p class="exp-desc">{{ e.desc }}</p>
          <div class="exp-tags">
            <span v-for="t in e.tags" :key="t" class="pill">{{ t }}</span>
          </div>
        </div>
      </li>
    </ol>
  </section>
</template>

<script setup lang="ts">
import SectionHeading from './SectionHeading.vue'
import { vReveal } from '@/composables/useRevealOnScroll'
import { experiences } from '@/data/profile'
</script>

<style scoped>
.exp-list { list-style: none; margin: 0; padding: 0; }
.exp-item {
  display: flex;
  gap: 1.5rem;
  padding: 1.6rem 1.25rem;
  margin: 0 -1.25rem;
  border-radius: 10px;
  position: relative;
  transition: background-color 0.25s ease, box-shadow 0.25s ease, opacity 0.3s ease;
}
.exp-item:hover {
  background-color: var(--bg-hover-card);
  box-shadow: var(--bg-hover-shadow);
}
/* v5 签名：group-hover dim */
.exp-list:hover .exp-item { opacity: 0.5; }
.exp-list:hover .exp-item:hover { opacity: 1; }
/* 条目底部渐变分隔线 */
.exp-item::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, rgba(136, 146, 176, 0.08), transparent 70%);
}
.exp-item:last-child::after { display: none; }
.exp-year {
  font-family: var(--font-mono);
  font-size: 11.5px;
  color: var(--text-2);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  width: 110px;
  flex-shrink: 0;
  padding-top: 5px;
  white-space: nowrap;
}
.exp-detail { flex: 1; min-width: 0; }
.exp-role-line {
  display: flex;
  align-items: baseline;
  gap: 0.4rem;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
}
.exp-role {
  font-size: 1.12rem;
  font-weight: 600;
  color: var(--text-bright);
}
.exp-company {
  font-size: 1.12rem;
  font-weight: 600;
  color: var(--accent-strong);
}
.exp-desc {
  font-size: 0.9rem;
  color: var(--text-2);
  line-height: 1.65;
  margin: 0 0 0.9rem;
}
.exp-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
@media (max-width: 480px) {
  .exp-item { flex-direction: column; gap: 0.4rem; }
  .exp-year { width: auto; }
}

</style>
