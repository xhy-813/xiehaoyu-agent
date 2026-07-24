<template>
  <div v-if="figureJson" class="result-chart">
    <div class="chart-container">
      <div ref="chartRef" class="chart-inner" />
    </div>
  </div>
  <div v-else class="empty-state">
    <n-text depth="3">暂无图表，提问需要可视化的问题后图表将在此展示</n-text>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'
import Plotly from 'plotly.js-dist'

const chat = useChatStore()
const chartRef = ref<HTMLDivElement>()

const figureJson = computed(() => {
  for (let i = chat.currentTrace.length - 1; i >= 0; i--) {
    const a = chat.currentTrace[i].artifact
    if (a?.figure_json) return a.figure_json
  }
  return null
})

function renderChart() {
  if (!figureJson.value || !chartRef.value) return
  const fig = JSON.parse(figureJson.value)
  Plotly.newPlot(chartRef.value, fig.data, fig.layout, {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d', 'sendDataToCloud'],
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#aaa', size: 11 },
    margin: { t: 40, r: 20, b: 50, l: 50 },
    xaxis: { gridcolor: 'rgba(255,255,255,0.06)', zerolinecolor: 'rgba(255,255,255,0.1)' },
    yaxis: { gridcolor: 'rgba(255,255,255,0.06)', zerolinecolor: 'rgba(255,255,255,0.1)' },
  })
}

watch(figureJson, () => nextTick(renderChart))
onMounted(() => nextTick(renderChart))
</script>

<style scoped>
.result-chart {
  padding: 0.5rem 0;
}
.chart-container {
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(0, 0, 0, 0.15);
}
.chart-inner {
  min-height: 320px;
}
.empty-state {
  text-align: center;
  padding: 1.5rem 0;
}
</style>