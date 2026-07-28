export interface QuickQuestion {
  label: string      // 短名（侧栏导航用）
  question: string   // 完整问题（chips 文案 + 实际发送内容）
  color: string      // 标识色
}

export interface QuickQuestionGroup {
  name: string
  questions: QuickQuestion[]
}

/** 欢迎屏提问示例：不分组平铺（豆包式：大标题 + 下方若干示例），数量在此增减即可 */
export const WELCOME_QUESTIONS: QuickQuestion[] = [
  { label: '自我介绍', question: '介绍一下你自己', color: '#0b7a55' },
  { label: '挑战项目', question: '你做过最有挑战的项目是什么？', color: '#0b7a55' },
  { label: '数据项目', question: '你做过哪些和数据相关的项目？', color: '#0b7a55' },
  { label: '每月订单', question: '2018 年每月订单数，帮我画个图', color: '#4f83e0' },
  { label: '各州分布', question: '订单主要来自哪些州？画个图分析一下', color: '#4f83e0' },
  { label: '品类订单', question: '订单量最高的商品品类是什么？画个图看看', color: '#4f83e0' },
]

/** 快捷提问分组（侧栏功能导航用）：呼应产品两大能力（个人 RAG 问答 / ChatBI 数据问答） */
export const QUICK_QUESTION_GROUPS: QuickQuestionGroup[] = [
  {
    name: '了解我',
    questions: [
      { label: '自我介绍', question: '介绍一下你自己', color: '#0b7a55' },
      { label: '技术栈', question: '你的技术栈是什么？', color: '#0b7a55' },
      { label: '挑战项目', question: '你做过最有挑战的项目是什么？', color: '#0b7a55' },
      { label: '数据项目', question: '你做过哪些和数据相关的项目？', color: '#0b7a55' },
    ],
  },
  {
    name: '试试数据问答',
    questions: [
      { label: '每月订单', question: '2018 年每月订单数，帮我画个图', color: '#4f83e0' },
      { label: '各州分布', question: '订单主要来自哪些州？画个图分析一下', color: '#4f83e0' },
      { label: '评分分布', question: '用户评分分布是怎样的？', color: '#4f83e0' },
      { label: '品类订单', question: '订单量最高的商品品类是什么？画个图看看', color: '#4f83e0' },
    ],
  },
]
