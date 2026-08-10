export interface QuickQuestion {
  label: string      // 短名（侧栏导航用）
  question: string   // 完整问题（chips 文案 + 实际发送内容）
}

/** 欢迎屏提问示例：不分组平铺（豆包式：大标题 + 下方若干示例），数量在此增减即可。
 *  08-09 方案 T4-5：从「3 条画个图」重设计为完整演示链——
 *  RAG 自我介绍/项目 → 查数出图 → 显式要求业务解读（确保触发 explain_result），
 *  并补一条联系方式问题承接 T2 的转化出口。 */
export const WELCOME_QUESTIONS: QuickQuestion[] = [
  { label: '自我介绍', question: '介绍一下你自己' },
  { label: '项目设计', question: 'Xiehaoyu-Agent 这个项目你是怎么设计实现的？' },
  { label: '订单趋势', question: '2018 年每月订单数，帮我画个图并解读一下趋势' },
  { label: '品类分析', question: '订单量最高的商品品类 Top 10 是什么？画个图并给出业务建议' },
  { label: '支付习惯', question: '客户主要用哪些支付方式？分析一下占比和分期习惯' },
  { label: '联系方式', question: '怎么联系你？' },
]

