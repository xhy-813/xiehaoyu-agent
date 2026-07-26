<template>
  <div v-if="dataArtifact" class="result-data">
    <n-collapse :default-expanded-names="[]">
      <n-collapse-item title="查看 SQL 语句" name="sql">
        <n-code
          :code="dataArtifact.sql || '(无)'"
          language="sql"
          :word-wrap="true"
        />
      </n-collapse-item>
    </n-collapse>
    <div class="table-wrapper">
      <n-data-table
        :columns="columns"
        :data="rows"
        :max-height="320"
        size="small"
        :bordered="false"
        striped
        virtual-scroll
      />
    </div>
    <div class="data-footer">
      <n-text depth="3" class="footer-text">
        {{ rows.length }} 行 · {{ columns.length }} 列
      </n-text>
    </div>
  </div>
  <div v-else class="empty-state">
    <n-text depth="3">暂无数据，提问后查询结果将在此展示</n-text>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useChatStore } from '@/stores/chat'

const chat = useChatStore()

const dataArtifact = computed(() => chat.dataArtifact)

const columns = computed(() => {
  const cols = dataArtifact.value?.df_columns || []
  return cols.map((c: string) => ({
    title: c,
    key: c,
    ellipsis: { tooltip: true },
    minWidth: 100,
    maxWidth: 300,
  }))
})

const rows = computed(() => {
  if (!dataArtifact.value?.df_json) return []
  try {
    return JSON.parse(dataArtifact.value.df_json)
  } catch {
    return []
  }
})
</script>

<style scoped>
.result-data {
  padding: 0.5rem 0;
}
.table-wrapper {
  margin-top: 0.5rem;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.data-footer {
  text-align: center;
  padding: 0.4rem 0;
}
.footer-text {
  font-size: 0.72rem;
}
.empty-state {
  text-align: center;
  padding: 1.5rem 0;
}
</style>