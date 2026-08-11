/** 个人内容静态数据（来源：data/知识库/简历、自我介绍、项目、工作经历 + 参考实现稿文案）。
 *  作品集区块全部从这里取数，改文案只动这个文件。 */

export interface Project {
  id: string
  title: string
  description: string
  icon: string        // 缩略图占位 emoji（无 image 时兜底）
  thumb: string       // 缩略图渐变底（CSS，无 image 时兜底）
  image?: string      // 项目截图（import 的静态资源，优先于 icon/thumb）
  stat: string        // 一行关键指标（星标行）
  tags: string[]
  link?: string
  linkLabel?: string  // link 悬停提示（如「查看完整报告」）
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
  // 侧栏社交图标指向各平台主页；项目仓库地址在 projects[0].link
  gitee: 'https://gitee.com/xiehaoyu12138',
  github: 'https://github.com/xhy-813',
  csdn: 'https://blog.csdn.net/2301_80330510?type=blog',
}

export const skillsFlat: string[] = [
  'Python', 'SQL', 'Pandas / NumPy', 'Hadoop / Hive', 'Spark', 'LangGraph',
  'FastAPI', 'Vue 3', 'Tableau / FineBI', 'ChromaDB', 'DeepSeek / Claude', 'Git / Docker',
]

// 项目截图（源文件在 data/作品集图片及链接/，压缩为 WebP 后入库）
import douyinSeedingImg from '@/assets/projects/douyin-seeding.webp'
import taobaoRfmImg from '@/assets/projects/taobao-rfm.webp'
import stockSentimentImg from '@/assets/projects/stock-sentiment.webp'
import k12DatawarehouseImg from '@/assets/projects/k12-datawarehouse.webp'

export const projects: Project[] = [  {
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
    image: douyinSeedingImg,
    stat: '447.5w 投放 · 1.2 亿声量',
    tags: ['Excel', 'FineBI', '星图数据', '漏斗分析', '归因分析'],
    link: 'https://jsu-sdais.feishu.cn/wiki/BMRDwePDIic0KZkQ23GcXmNZnnh',
    linkLabel: '查看完整复盘报告（飞书）',
  },
  {
    id: 'taobao-rfm',
    title: '淘宝用户价值分层与精准营销',
    description:
      '基于用户行为数据构建 RFM 模型，划分 8 类用户群体。发现浏览到购买转化率仅 9.47%、82.65% 商品仅被购买一次，针对五类重点人群输出差异化策略组合。',
    icon: '📈',
    thumb: 'linear-gradient(135deg, #1f2d3d, #0f1820)',
    image: taobaoRfmImg,
    stat: '预估 ROI +33.5%',
    tags: ['Python', 'Pandas', 'RFM 模型', 'Seaborn', 'Matplotlib'],
    link: 'https://jsu-sdais.feishu.cn/wiki/EpWLwRxFei7VzcknQDRcYBIinxd',
    linkLabel: '查看完整分析报告（飞书）',
  },
  {
    id: 'k12-datawarehouse',
    title: 'K12 线上教育场景数据仓库开发与经营分析',
    description:
      '基于 50 万条 K12 订单数据搭建 ODS→DWD→DWS→DIM 四层 Hive 数仓，解决联报课程业绩归属问题，Hive 调优整体提速 80%，DataX 对接 PowerBI 交付 6 页经营看板。',
    icon: '🏫',
    thumb: 'linear-gradient(135deg, #1a2a4a, #0d1a30)',
    image: k12DatawarehouseImg,
    stat: '50 万条订单 · ETL 提速 80% · 存储减少 75%',
    tags: ['Hive', 'HDFS', 'DataX', 'MySQL', 'PowerBI', 'DAX', 'Java UDF', 'Shell'],
    link: 'https://jsu-sdais.feishu.cn/wiki/Qlm7wCH7miaCfAk4zZec1b58nxg',
    linkLabel: '查看经营分析看板（飞书）',
  },
  {
    id: 'stock-sentiment',
    title: '股市舆情分析系统',
    description:
      '采集 3.2 万条股吧评论，人工标注 2500 条样本微调 BERT 中文金融情感分类器（准确率 90%+），构建日度情绪指数并验证与沪深 300 的相关性。',
    icon: '💹',
    thumb: 'linear-gradient(135deg, #1d3a2f, #0d201a)',
    image: stockSentimentImg,
    stat: '3.2 万条评论 · 准确率 90%+',
    tags: ['Python', 'BERT', 'NLP', 'Scrapy', 'StatsModels'],
    link: 'https://b.datav.run/share/page/a51917cdc74ffa315e716ec319c15f90',
    linkLabel: '查看 A 股数据看板（DataV）',
  },
]

export const experiences: Experience[] = [
  {
    company: '龙腾出行',
    role: '数据实习生',
    period: '2026.04 — 2026.08',
    desc: '基于 DataPipeline 分层架构打通多源 API 采集清洗入库全链路，覆盖国内外十万余条数据；设计四层数据完整性评估脚本并搭建 FineBI 实时看板；对 POI 匹配失败案例做聚类归因，定位根因后准确率提升 62%；基于千问大模型搭建「生成→验证→重生成」AI 清洗流程。',
    tags: ['Python', 'DataPipeline', 'FineBI', 'ETL', '大模型应用'],
  },
  {
    company: '吉首大学',
    role: '数据科学与大数据技术',
    period: '2023.09 — 2027.06',
    desc: '专业排名前 5%（GPA 3.7）；连续三年获一等奖学金，并获国家励志奖学金；全国大学生数学建模竞赛省级一等奖、计算机设计大赛中南赛区二等奖。核心课程涵盖应用统计学、数据清洗与可视化、数据仓库、分布式计算（Hadoop / Spark）等。',
    tags: ['数学建模', '数据仓库','数据清洗与可视化', 'Hadoop' , 'Spark'],
  },
]
