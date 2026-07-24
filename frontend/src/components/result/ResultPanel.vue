<template>
  <div class="result-panel">
    <div class="panel-header">
      <n-text depth="1" strong>结果面板</n-text>
      <n-text depth="3" class="panel-subtitle">数据 · 图表 · 轨迹</n-text>
    </div>

    <ResultSummary />

    <n-tabs type="segment" size="small" animated class="panel-tabs">
      <n-tab-pane name="data" tab="数据">
        <ResultData />
      </n-tab-pane>
      <n-tab-pane name="chart" tab="图表">
        <ResultChart />
      </n-tab-pane>
      <n-tab-pane name="trace" tab="轨迹">
        <ResultTrace />
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

<script setup lang="ts">
import ResultSummary from './ResultSummary.vue'
import ResultData from './ResultData.vue'
import ResultChart from './ResultChart.vue'
import ResultTrace from './ResultTrace.vue'
</script>

<style scoped>
.result-panel {
  padding: 1rem;
}
.panel-header {
  padding: 0.25rem 0 0.5rem;
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}
.panel-subtitle {
  font-size: 0.75rem;
}
.panel-tabs {
  margin-top: 0.25rem;
}
</style>