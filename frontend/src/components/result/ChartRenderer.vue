<template>
  <div ref="rootRef" class="chart-renderer" />
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import Plotly from 'plotly.js-dist'

const props = defineProps<{ figureJson: string }>()

const rootRef = ref<HTMLDivElement>()
let chartInstance: any = null

function render() {
  const el = rootRef.value
  if (!el || !props.figureJson) return
  if (el.offsetWidth === 0 || el.offsetHeight === 0) {
    requestAnimationFrame(render)
    return
  }
  if (chartInstance) {
    Plotly.purge(el)
    chartInstance = null
  }
  const fig = JSON.parse(props.figureJson)
  Plotly.newPlot(el, fig.data, fig.layout, {
    responsive: true, displayModeBar: true, displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d', 'sendDataToCloud'],
    paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
    font: { color: '#aaa', size: 11 },
    margin: { t: 40, r: 20, b: 50, l: 50 },
  }).then((plot: any) => { chartInstance = plot })
}

onMounted(() => {
  requestAnimationFrame(() => setTimeout(render, 50))
})

watch(() => props.figureJson, () => {
  setTimeout(render, 100)
})

onUnmounted(() => {
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