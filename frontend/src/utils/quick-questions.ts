export interface QuickQuestion {
  label: string      // 短名（侧栏导航用）
  question: string   // 完整问题（chips 文案 + 实际发送内容）
}

/** 欢迎屏提问示例：不分组平铺（豆包式：大标题 + 下方若干示例），数量在此增减即可 */
export const WELCOME_QUESTIONS: QuickQuestion[] = [
  { label: '自我介绍', question: '介绍一下你自己' },
  { label: '技能亮点', question: '你有哪些技术亮点，擅长什么方向？' },
  { label: 'K12 数仓', question: '你的 K12 数仓项目具体做了什么？' },
  { label: '每月订单', question: '2018 年每月订单数，帮我画个图' },
  { label: '品类排名', question: '订单量最高的商品品类 Top 10 是什么？画个图看看' },
  { label: '各州分布', question: '订单主要来自哪些州？画个图分析一下' },
]

