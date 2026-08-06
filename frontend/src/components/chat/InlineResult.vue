<template>
  <div class="inline-result">
    <!-- Chart -->
    <div v-if="chartJson" class="ir-section">
      <div class="ir-section-header">
        <n-icon size="16" color="#64ffda"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg></n-icon>
        <span>图表</span>
        <n-tag size="tiny" :bordered="false" type="success">{{ chartTypeLabel }}</n-tag>
      </div>
      <div class="ir-chart-wrap">
        <ChartRenderer :figure-json="chartJson" />
      </div>
    </div>

    <!-- Data table -->
    <div v-if="dataArtifact" class="ir-section">
      <div class="ir-section-header">
        <n-icon size="16" color="#64b5f6"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M4 6h16v2H4zm0 5h16v2H4zm0 5h16v2H4z"/></svg></n-icon>
        <span>数据表</span>
        <n-tag size="tiny" :bordered="false">{{ rowsCols }}</n-tag>
      </div>
      <n-collapse :default-expanded-names="[]">
        <n-collapse-item title="SQL 语句" name="sql">
          <n-code :code="dataArtifact.sql || '(无)'" language="sql" :word-wrap="true" />
        </n-collapse-item>
      </n-collapse>
      <div class="ir-table-wrap">
        <n-data-table :columns="columns" :data="rows" :max-height="260" size="small" :bordered="false" striped virtual-scroll />
      </div>
    </div>

    <!-- Trace: collapsible -->
    <n-collapse :default-expanded-names="[]">
      <n-collapse-item name="trace">
        <template #header>
          <div class="ir-section-header">
            <n-icon size="16" color="#ffb86c"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg></n-icon>
            <span>执行轨迹</span>
            <n-tag size="tiny" :bordered="false" type="warning">{{ trace.length }} 步</n-tag>
          </div>
        </template>
        <div class="ir-trace">
          <div v-for="(step, i) in trace" :key="i" class="irt-step">
            <div class="irt-line">
              <div class="irt-dot" :style="{ background: stepColor(step.tool) }" />
              <div v-if="i < trace.length - 1" class="irt-connector" />
            </div>
            <div class="irt-body">
              <div class="irt-header">
                <n-tag size="tiny" :bordered="false" :type="tagType(step.tool)" round>{{ toolLabel(step.tool) }}</n-tag>
                <span class="irt-num">Step {{ i + 1 }}</span>
              </div>
              <div class="irt-summary">{{ step.summary }}</div>
            </div>
          </div>
        </div>
      </n-collapse-item>
    </n-collapse>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import ChartRenderer from '@/components/result/ChartRenderer.vue'
import type { ToolTrace } from '@/stores/chat'
import { CHART_LABELS, toolLabel, tagType, stepColor } from '@/utils/tool-constants'
import { findDataArtifact, findChartArtifact } from '@/utils/artifact'

const props = defineProps<{ trace: ToolTrace[] }>()

const dataArtifact = computed(() => findDataArtifact(props.trace))
const chartArtifact = computed(() => findChartArtifact(props.trace))
const chartJson = computed(() => chartArtifact.value?.figure_json || null)
const columns = computed(() => {
  const cols = dataArtifact.value?.df_columns || []
  return cols.map((c: string) => ({ title: c, key: c, ellipsis: { tooltip: true }, minWidth: 80, maxWidth: 300 }))
})
const rows = computed(() => {
  if (!dataArtifact.value?.df_json) return []
  try { return JSON.parse(dataArtifact.value.df_json) } catch { return [] }
})
const rowsCols = computed(() => {
  const a = dataArtifact.value
  return a?.df_shape ? `${a.df_shape.rows}×${a.df_shape.cols}` : '--'
})
const chartTypeLabel = computed(() => {
  const t = chartArtifact.value?.chart_type || ''
  return CHART_LABELS[t] || t || '--'
})
</script>

<style scoped>
.inline-result {
  margin-top: 0.75rem;
  border: 1px solid var(--border);
  background: var(--bg-card);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: var(--result-card-shadow);
}
.ir-section {
  border-bottom: 1px solid var(--border);
}
.ir-section:last-child {
  border-bottom: none;
}
.ir-section-header {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.55rem 0.8rem; font-size: 0.83rem; color: var(--text-2);
  background: var(--bg-subtle);
}
.ir-chart-wrap { padding: 0.5rem; min-height: 300px; }
.ir-trace { padding: 0.5rem 0.8rem; }
.irt-step { display: flex; gap: 0.5rem; animation: fadeIn 0.25s ease-out; }
.irt-line { display: flex; flex-direction: column; align-items: center; width: 12px; flex-shrink: 0; }
.irt-dot { width: 8px; height: 8px; border-radius: 50%; margin-top: 5px; }
.irt-connector { width: 1px; flex: 1; background: var(--border); margin: 3px 0; }
.irt-body { flex: 1; padding: 0.2rem 0 0.7rem; }
.irt-header { display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.2rem; }
.irt-num { font-size: 0.68rem; color: var(--text-3); }
.irt-summary { font-size: 0.78rem; color: var(--text-2); line-height: 1.4; word-break: break-word; }
.ir-section :deep(.n-collapse-item__content-wrapper) {
  transition: max-height 0.3s ease, opacity 0.3s ease;
}
</style>