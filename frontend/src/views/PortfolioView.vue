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
  padding: 10vh 8vw 10vh 4vw;
  display: flex;
  flex-direction: column;
  gap: 80px;
}
@media (max-width: 1200px) {
  .right-col { margin-left: 38%; width: 62%; padding-right: 6vw; }
}
@media (max-width: 980px) {
  .right-col { margin-left: 0; width: 100%; padding: 6vh 6vw; gap: 56px; }
}
@media (max-width: 480px) {
  .right-col { padding: 5vh 5vw; }
}
</style>
