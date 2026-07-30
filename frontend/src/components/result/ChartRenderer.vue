<template>
  <div ref="rootRef" class="chart-renderer" />
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import type Plotly from 'plotly.js-dist'

const props = defineProps<{ figureJson: string }>()

const rootRef = ref<HTMLDivElement>()
let chartInstance: Plotly.PlotlyHTMLElement | null = null
let rafId = 0
let resizeObserver: ResizeObserver | null = null

// plotly.js-dist 体积大，按需动态加载（仅真正出图时加载一次）
let plotlyPromise: Promise<typeof Plotly> | null = null
let PlotlyRef: typeof Plotly | null = null

function ensurePlotly(): Promise<typeof Plotly> {
  if (!plotlyPromise) {
    plotlyPromise = import('plotly.js-dist').then((m) => {
      PlotlyRef = (m as { default: typeof Plotly }).default || m
      return PlotlyRef!
    })
  }
  return plotlyPromise
}

async function render() {
  const el = rootRef.value
  if (!el || !props.figureJson) return
  if (el.offsetWidth === 0 || el.offsetHeight === 0) {
    rafId = requestAnimationFrame(render)
    return
  }
  const Plotly = await ensurePlotly()
  if (chartInstance) {
    Plotly.purge(el)
    chartInstance = null
  }
  try {
    const fig = JSON.parse(props.figureJson)
    const layout = {
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      font: { color: '#5c6370', size: 11 },
      margin: { t: 40, r: 20, b: 50, l: 50 },
      ...fig.layout,
    }
    Plotly.newPlot(el, fig.data, layout, {
      responsive: true,
      displaylogo: false,
      displayModeBar: false,
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
      if (chartInstance && rootRef.value && PlotlyRef) {
        PlotlyRef.Plots.resize(rootRef.value)
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
  if (chartInstance && rootRef.value && PlotlyRef) {
    PlotlyRef.purge(rootRef.value)
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
