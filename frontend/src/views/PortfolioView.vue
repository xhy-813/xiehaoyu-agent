<template>
  <div class="portfolio">
    <MouseSpotlight />
    <SiteSidebar />
    <main class="right-col">
      <AboutSection />
      <ExperienceSection />
      <ProjectsSection />
      <ChatSection />
      <SiteFooter />
    </main>
  </div>
</template>

<script setup lang="ts">
import MouseSpotlight from '@/components/portfolio/MouseSpotlight.vue'
import SiteSidebar from '@/components/portfolio/SiteSidebar.vue'
import AboutSection from '@/components/portfolio/AboutSection.vue'
import ExperienceSection from '@/components/portfolio/ExperienceSection.vue'
import ProjectsSection from '@/components/portfolio/ProjectsSection.vue'
import ChatSection from '@/components/portfolio/ChatSection.vue'
import SiteFooter from '@/components/portfolio/SiteFooter.vue'
</script>

<style scoped>
.portfolio {
  min-height: 100vh;
  background: var(--bg-base);
}
/* 右列：margin-left 与 SiteSidebar 宽度联动（42% / ≤1200px 38% / ≤980px 单列） */
.right-col {
  margin-left: 42%;
  width: 58%;
  min-width: 0;
  /* 内容区右侧保留充足留白，避免文字贴边；顶部留 10vh 与左栏对齐 */
  padding: 10vh clamp(2rem, 5vw, 80px) 10vh clamp(1.5rem, 3vw, 48px);
  display: flex;
  flex-direction: column;
  gap: 80px;
  /* 限制内容区最大宽度，宽屏时文字行长不超阅读舒适区 */
  max-width: calc(42% + 760px);
}
@media (max-width: 1200px) {
  .right-col { margin-left: 38%; width: 62%; max-width: none; }
}
@media (max-width: 980px) {
  .right-col { margin-left: 0; width: 100%; padding: 6vh 6vw; gap: 56px; max-width: none; }
}
@media (max-width: 480px) {
  .right-col { padding: 5vh 5vw; gap: 48px; }
}
</style>
