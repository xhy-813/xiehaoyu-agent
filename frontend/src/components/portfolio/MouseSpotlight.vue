<template>
  <div id="spotlight" aria-hidden="true" />
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount } from 'vue'

onMounted(() => {
  if (
    matchMedia('(prefers-reduced-motion: reduce)').matches ||
    matchMedia('(pointer: coarse)').matches
  ) {
    return
  }

  const el = document.getElementById('spotlight')
  if (!el) return

  let mx = window.innerWidth / 2
  let my = window.innerHeight / 2
  let ticking = false
  let rafId = 0

  function update() {
    el!.style.setProperty('--mx', mx + 'px')
    el!.style.setProperty('--my', my + 'px')
    ticking = false
  }

  // initial render at viewport center
  update()

  function onMouseMove(e: MouseEvent) {
    mx = e.clientX
    my = e.clientY
    if (!ticking) {
      rafId = requestAnimationFrame(update)
      ticking = true
    }
  }

  window.addEventListener('mousemove', onMouseMove, { passive: true })

  onBeforeUnmount(() => {
    window.removeEventListener('mousemove', onMouseMove)
    if (rafId) cancelAnimationFrame(rafId)
  })
})
</script>

<style scoped>
#spotlight {
  position: fixed;
  inset: 0;
  z-index: 9999;
  pointer-events: none;
  background: radial-gradient(
    700px circle at var(--mx, 50vw) var(--my, 50vh),
    rgba(100, 255, 218, 0.22),
    rgba(100, 255, 218, 0.08) 25%,
    transparent 65%
  );
  will-change: background;
}
@media (hover: none), (pointer: coarse) {
  #spotlight { display: none; }
}
@media (prefers-reduced-motion: reduce) {
  #spotlight { display: none; }
}
</style>