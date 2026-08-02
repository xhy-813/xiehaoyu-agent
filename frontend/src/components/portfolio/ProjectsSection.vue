<template>
  <section id="projects" v-reveal>
    <SectionHeading num="03." title="项目" />
    <div class="proj-grid stagger">
      <article v-for="p in projects" :key="p.id" class="proj-card" v-reveal>
        <div class="proj-thumb" :style="{ background: p.thumb }" aria-hidden="true">
          <span class="proj-thumb-icon">{{ p.icon }}</span>
        </div>
        <div class="proj-info">
          <div class="proj-title-row">
            <h3 class="proj-title">{{ p.title }}</h3>
            <span v-if="p.featured" class="proj-badge">你正在使用它</span>
            <a v-if="p.link" :href="p.link" target="_blank" rel="noopener" class="proj-link" aria-label="查看项目">↗</a>
          </div>
          <p class="proj-desc">{{ p.description }}</p>
          <span class="proj-stat">
            <svg viewBox="0 0 24 24" width="13" height="13" stroke="currentColor" fill="none" stroke-width="2" aria-hidden="true"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
            {{ p.stat }}
          </span>
          <div class="proj-tags">
            <span v-for="t in p.tags" :key="t" class="pill">{{ t }}</span>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import SectionHeading from './SectionHeading.vue'
import { vReveal } from '@/composables/useRevealOnScroll'
import { projects } from '@/data/profile'
</script>

<style scoped>
.proj-grid { display: flex; flex-direction: column; }
.proj-card {
  display: flex;
  gap: 1.4rem;
  padding: 1.5rem 1.25rem;
  margin: 0 -1.25rem;
  border-radius: 10px;
  transition: background-color 0.25s ease, box-shadow 0.25s ease, opacity 0.3s ease;
}
.proj-card:hover {
  background-color: rgba(17, 34, 64, 0.5);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.18);
}
/* v5 签名：group-hover dim */
.proj-grid:hover .proj-card { opacity: 0.5; }
.proj-grid:hover .proj-card:hover { opacity: 1; }
.proj-thumb {
  width: 110px;
  height: 78px;
  border-radius: 6px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  /* v5 手法：默认去饱和，hover 恢复全彩 */
  filter: saturate(0.55) contrast(1.02);
  transition: filter 0.3s ease;
}
.proj-card:hover .proj-thumb { filter: saturate(1) contrast(1); }
.proj-thumb-icon {
  font-size: 22px;
  opacity: 0.4;
}
.proj-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.proj-title-row {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.proj-title {
  font-size: 1.18rem;
  font-weight: 600;
  color: var(--text-bright);
  line-height: 1.3;
  margin: 0;
}
.proj-badge {
  font-size: 0.68rem;
  font-family: var(--font-mono);
  color: var(--accent-strong);
  border: 1px solid var(--accent-border);
  border-radius: var(--radius-pill);
  padding: 0.1rem 0.55rem;
  font-weight: 400;
}
.proj-link {
  color: var(--accent-strong);
  text-decoration: none;
  font-size: 0.9rem;
  transition: transform 0.2s ease;
  display: inline-block;
}
.proj-link:hover { transform: translateX(3px); }
.proj-desc {
  font-size: 0.85rem;
  color: var(--text-2);
  line-height: 1.6;
  margin: 0;
}
.proj-stat {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--text-2);
  display: flex;
  align-items: center;
  gap: 0.3rem;
}
.proj-stat svg { stroke: var(--accent-strong); }
.proj-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}
@media (max-width: 980px) {
  .proj-card { flex-direction: column; padding: 1.25rem; margin: 0; }
  .proj-thumb { width: 100%; height: 160px; }
}
</style>
