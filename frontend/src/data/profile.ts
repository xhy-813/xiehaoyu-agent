/** 个人内容静态数据（来源：data/知识库/简历、自我介绍、项目、工作经历 + 参考实现稿文案）。
 *  作品集区块全部从这里取数，改文案只动这个文件。 */

export interface Project {
  id: string
  title: string
  description: string
  icon: string        // 缩略图占位 emoji
  thumb: string       // 缩略图渐变底（CSS）
  stat: string        // 一行关键指标（星标行）
  tags: string[]
  link?: string
  featured?: boolean
}

export interface Experience {
  company: string
  role: string
  period: string
  desc: string
  tags: string[]
}

export const profile = {
  name: '谢浩宇',
  role: '数据工程师 · AI 实践者',
  tagline: '我专注于数据工程与智能分析，擅长从原始数据中提炼洞察，用 AI 工具放大生产力，构建可解释、可落地的数据产品。',
  // 段落含 <strong> 高亮（静态可信内容，AboutSection 用 v-html 渲染）
  intro: [
    '你好！我是<strong>谢浩宇</strong>，来自吉首大学<strong>数据科学与大数据技术</strong>专业，目前本科在读，专业排名前 <strong>5%</strong>。',
    '我对数据的热情始于对「数字背后故事」的好奇——从一条 SQL 查询到完整的数仓分层，从一张散点图到驱动业务决策的指标体系，我喜欢把杂乱的数据变成清晰的洞察。',
    '目前在<strong>龙腾出行 AI 研发部</strong>担任数据实习生，负责数据管道建设、数据质量监控、归因分析和 AI 赋能等工作。此前独立开发了<strong>Xiehaoyu-Agent</strong>个人智能体系统——一个基于 LLM Agent 的 ChatBI 应用，集成了 RAG 知识库检索、Text2SQL 引擎和自动可视化能力。',
    '工作之外，我喜欢研究新的 AI 工具和工作流，探索如何将大语言模型融入日常数据分析流程中。也热衷于参加数学建模和数据竞赛，享受从问题抽象到方案落地的全过程。',
  ],
  email: 'xiehaoyu12138@163.com',
  wechat: 'xhy18711807395',
  repo: 'https://gitee.com/xiehaoyu12138/xiehaoyu-agent/tree/main/',
  repoLabel: '代码仓库',
}

export const skillsFlat: string[] = [
  'Python', 'SQL', 'Pandas / NumPy', 'Hadoop / Hive', 'Spark', 'LangGraph',
  'FastAPI', 'Vue 3', 'Tableau / FineBI', 'ChromaDB', 'DeepSeek / Claude', 'Git / Docker',
]

export const projects: Project[] = [
  {
    id: 'xiehaoyu-agent',
    title: 'Xiehaoyu-Agent',
    description:
      '基于 LLM Agent 的个人智能体与 ChatBI 系统。LangGraph 状态机驱动多 Tool 编排，集成 RAG 个人知识库检索、Text2SQL 查数引擎与自动可视化。你正在使用的这个网站就是它。',
    icon: '🤖',
    thumb: 'linear-gradient(135deg, #1a3a5c, #0d2137)',
    stat: '99,441 订单 · 9 表关联',
    tags: ['Python', 'LangGraph', 'DeepSeek', 'ChromaDB', 'FastAPI', 'Vue 3', 'Plotly'],
    link: 'https://gitee.com/xiehaoyu12138/xiehaoyu-agent/tree/main/',
  },
  {
    id: 'douyin-seeding',
    title: '抖音达人种草复盘与策略分析',
    description:
      '对 447.5 万投放费用、1.2 亿声量做深度归因分析。竞品对标转化率达行业均值 6 倍、单位成本仅行业 1/12；发现 34% 达人单位转化成本超 100 元/人，提出小博主优先策略并建立实时监控看板。',
    icon: '📊',
    thumb: 'linear-gradient(135deg, #2d1f3d, #151020)',
    stat: '447.5w 投放 · 1.2 亿声量',
    tags: ['Excel', 'FineBI', '星图数据', '漏斗分析', '归因分析'],
  },
  {
    id: 'taobao-rfm',
    title: '淘宝用户价值分层与精准营销',
    description:
      '基于用户行为数据构建 RFM 模型，划分 8 类用户群体。发现浏览到购买转化率仅 9.47%、82.65% 商品仅被购买一次，针对五类重点人群输出差异化策略组合。',
    icon: '📈',
    thumb: 'linear-gradient(135deg, #1f2d3d, #0f1820)',
    stat: '预估 ROI +33.5%',
    tags: ['Python', 'Pandas', 'RFM 模型', 'Seaborn', 'Matplotlib'],
  },
  {
    id: 'stock-sentiment',
    title: '股市舆情分析系统',
    description:
      '采集 3.2 万条股吧评论，人工标注 2500 条样本微调 BERT 中文金融情感分类器（准确率 90%+），构建日度情绪指数并验证与沪深 300 的相关性。',
    icon: '💹',
    thumb: 'linear-gradient(135deg, #1d3a2f, #0d201a)',
    stat: '3.2 万条评论 · 准确率 90%+',
    tags: ['Python', 'BERT', 'NLP', 'Scrapy', 'StatsModels'],
  },
]

export const experiences: Experience[] = [
  {
    company: '龙腾出行',
    role: '数据实习生',
    period: '2026.04 — 至今',
    desc: '基于 DataPipeline 分层架构打通多源 API 采集清洗入库全链路，覆盖国内外十万余条数据；设计四层数据完整性评估脚本并搭建 FineBI 实时看板；对 POI 匹配失败案例做聚类归因，定位根因后准确率提升 62%；基于千问大模型搭建「生成→验证→重生成」AI 清洗流程。',
    tags: ['Python', 'DataPipeline', 'FineBI', '归因分析', '千问大模型'],
  },
  {
    company: '吉首大学',
    role: '本科在读',
    period: '2024.09 — 至今',
    desc: '数据科学与大数据技术专业，专业排名前 5%。核心课程涵盖数据结构、数据库原理、机器学习、分布式计算（Hadoop / Spark）、数据可视化等。参与数学建模、数据分析、Kaggle 竞赛，多次获得校级和省级奖项。',
    tags: ['Hadoop', 'Spark', '机器学习', '数学建模'],
  },
]
