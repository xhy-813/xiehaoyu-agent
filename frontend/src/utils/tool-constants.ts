/** Shared tool display constants used across ChatMessage, ResultTrace, and
 * ResultSummary components.  Changing a tool name or colour here updates
 * every component that references it. */

export const TOOL_LABELS: Record<string, string> = {
  query_data: '查询数据',
  visualize: '生成图表',
  introduce_me: '检索知识库',
  explain_result: '解读结果',
}

export const TAG_MAP: Record<string, 'info' | 'success' | 'warning' | 'default'> = {
  query_data: 'info',
  visualize: 'success',
  introduce_me: 'warning',
  explain_result: 'default',
}

export const STEP_COLORS: Record<string, string> = {
  query_data: '#63a4ff',
  visualize: '#63e2b7',
  introduce_me: '#ffb74d',
  explain_result: '#ce93d8',
}

export const CHART_LABELS: Record<string, string> = {
  indicator: '指标卡',
  line: '折线图',
  bar: '柱状图',
  scatter: '散点图',
  table: '表格',
}

/** Human-readable label for a tool name. */
export function toolLabel(t: string): string {
  return TOOL_LABELS[t] || t
}

/** Naive UI tag type for a tool name. */
export function tagType(t: string): 'info' | 'success' | 'warning' | 'default' {
  return TAG_MAP[t] || 'default'
}

/** Timeline dot colour for a tool name. */
export function stepColor(t: string): string {
  return STEP_COLORS[t] || '#888'
}