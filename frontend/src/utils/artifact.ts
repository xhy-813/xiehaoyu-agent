import type { Artifact } from '@/utils/sse'
import type { ToolTrace } from '@/stores/chat'

/** 倒序查找 trace 中最后一个满足条件的 artifact（取最新一次结果） */
export function findLastArtifact(
  trace: ToolTrace[],
  predicate: (a: Artifact) => boolean,
): Artifact | null {
  for (let i = trace.length - 1; i >= 0; i--) {
    const a = trace[i].artifact
    if (a && predicate(a)) return a
  }
  return null
}

/** 最后一个含 df_json 的 artifact（最新一次数据查询结果） */
export const findDataArtifact = (t: ToolTrace[]) =>
  findLastArtifact(t, a => !!a.df_json)

/** 最后一个含 figure_json 的 artifact（最新一次可视化结果） */
export const findChartArtifact = (t: ToolTrace[]) =>
  findLastArtifact(t, a => !!a.figure_json)

/** 最后一个含非空 citations 的 artifact（最新一次 RAG 引用来源，08-09 方案 T4-1） */
export const findCitationArtifact = (t: ToolTrace[]) =>
  findLastArtifact(t, a => Array.isArray(a.citations) && a.citations.length > 0)
