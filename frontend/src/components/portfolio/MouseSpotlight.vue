<template><!-- spotlight: CSS vars injected onto :root, gradient lives in PortfolioView --></template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount } from 'vue'

onMounted(() => {
  if (
    matchMedia('(prefers-reduced-motion: reduce)').matches ||
    matchMedia('(pointer: coarse)').matches
  ) {
    return
  }

  const root = document.documentElement
  let mx = window.innerWidth / 2
  let my = window.innerHeight / 2
  let ticking = false
  let rafId = 0

  function update() {
    root.style.setProperty('--spotlight-x', mx + 'px')
    root.style.setProperty('--spotlight-y', my + 'px')
    ticking = false
  }

  // seed position so there's no jump on first move
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
