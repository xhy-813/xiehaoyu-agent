<template>
  <div ref="rootRef" class="chart-renderer" />
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import Plotly from 'plotly.js-dist'

const props = defineProps<{ figureJson: string }>()

const rootRef = ref<HTMLDivElement>()
let chartInstance: any = null
let rafId = 0
let resizeObserver: ResizeObserver | null = null

function render() {
  const el = rootRef.value
  if (!el || !props.figureJson) return
  if (el.offsetWidth === 0 || el.offsetHeight === 0) {
    rafId = requestAnimationFrame(render)
    return
  }
  if (chartInstance) {
    Plotly.purge(el)
    chartInstance = null
  }
  try {
    const fig = JSON.parse(props.figureJson)
    Plotly.newPlot(el, fig.data, fig.layout, {
      responsive: true, displayModeBar: true, displaylogo: false,
      modeBarButtonsToRemove: ['lasso2d', 'select2d', 'sendDataToCloud'],
      paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
      font: { color: '#aaa', size: 11 },
      margin: { t: 40, r: 20, b: 50, l: 50 },
    }).then((plot: any) => { chartInstance = plot })
  } catch {
    // Malformed figure JSON; leave the chart area empty.
  }
}

onMounted(() => {
  rafId = requestAnimationFrame(() => setTimeout(render, 50))
  // Re-render chart when the container size changes (window resize, etc.)
  if (rootRef.value) {
    resizeObserver = new ResizeObserver(() => {
      if (chartInstance && rootRef.value) {
        Plotly.Plots.resize(rootRef.value)
      }
    })
    resizeObserver.observe(rootRef.value)
  }
})

watch(() => props.figureJson, () => {
  setTimeout(render, 100)
})

onUnmounted(() => {
  cancelAnimationFrame(rafId)
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (chartInstance && rootRef.value) {
    Plotly.purge(rootRef.value)
    chartInstance = null
  }
})
</script>

<style scoped>
.chart-renderer {
  min-height: 300px;
  width: 100%;
}
</style>