# 方案 E：全面品牌形象整合

> **工时**：~4-5h | **改动文件**：7+ 个 | **难度**：★★★★☆

## 概述

将方案 A～D 的优点整合，形成一套完整的个人品牌形象系统。这是一个"全栈"方案——从登录页到聊天界面，从侧边栏到个人主页，每个页面都有你的个人形象露出。

## 整体改造清单

| 文件 | 改动内容 | 使用照片 |
|------|----------|----------|
| `LoginView.vue` | 左右分栏 + 全身照 | 全身照 |
| `ChatSidebar.vue` | 头像替换 + 个人信息卡 | 证件照 |
| `WelcomeCard.vue` | 头像 + 个人信息展示 | 生活照 |
| `ChatMessage.vue` | AI 头像替换为照片 | 证件照 |
| `ProfileView.vue` | 新增个人主页 | 生活照 |
| `router/index.ts` | 新增 `/profile` 路由 | - |
| `src/data/profile.ts` | 新增个人信息配置 | - |
| `App.vue` | 可选：全局 favicon 更新 | 证件照 |

## 详细设计

### 1. 个人信息配置文件（基础设施）— `src/data/profile.ts`

```ts
export const profile = {
  // 基本信息
  name: '谢浩宇',
  nameEn: 'Xie Haoyu',
  title: '数据科学与大数据技术',
  school: '吉首大学',
  grade: '2023 级本科',
  location: '广州 / 深圳',
  email: 'email@example.com',
  github: 'https://github.com/yourname',
  status: '正在找数据分析 / 数据工程方向实习',

  // 照片资源路径
  avatar: new URL('@/assets/avatar.jpg', import.meta.url).href,
  lifestyle: new URL('@/assets/lifestyle.jpg', import.meta.url).href,
  fullbody: new URL('@/assets/fullbody.jpg', import.meta.url).href,

  // 技能
  skills: [
    'Python', 'SQL', 'Pandas', 'Scrapy', 'Tableau', 'FineBI',
    'Hive', 'Spark', 'Docker', 'Git', 'LLM API', 'LangChain', 'LangGraph',
  ],

  // 项目经历
  projects: [
    {
      name: 'K12 数仓与 PowerBI 可视化看板',
      desc: '基于 K12 线上教育场景，设计数仓分层架构，使用 Hive 进行 ETL 工程，通过 PowerBI 构建可视化看板。',
      tech: ['Hive', 'SQL', 'PowerBI', '数据仓库'],
      highlight: '独立完成数仓建模与报表开发',
    },
    {
      name: '郑州机场知识库系统',
      desc: '基于 RAG 架构的机场服务知识库，支持自然语言查询机场服务、乘机指南、行李运输等信息。',
      tech: ['Python', 'LangChain', 'ChromaDB', 'RAG'],
      highlight: '实现多文档类型的知识检索',
    },
    {
      name: 'Xiehaoyu-Agent（本项目）',
      desc: '基于 LangGraph 的 LLM Agent 系统，包含个人数字分身和 ChatBI 两大功能模块。',
      tech: ['LangGraph', 'DeepSeek', 'Vue 3', 'FastAPI'],
      highlight: '全栈独立开发，前后端分离架构',
    },
  ],

  // 实习经历
  experience: [
    {
      company: '龙腾出行',
      role: '数据工程实习生',
      period: '2025.03 - 2025.09',
      desc: '负责 POI 匹配优化、数据管道维护、LLM 数据清洗、itinerary 数据入库重构等工作。',
      highlights: ['POI 匹配准确率提升', '数据管道配置统一规整', 'LLM 清洗逻辑设计'],
    },
  ],

  // 社交链接
  socialLinks: [
    { icon: 'github', label: 'GitHub', url: 'https://github.com/yourname' },
    { icon: 'email', label: 'Email', url: 'mailto:email@example.com' },
  ],
}
```

### 2. 登录页 — `LoginView.vue`

采用方案 B 的左右分栏设计，但数据从 `profile.ts` 读取：

```
┌──────────────────────────────────────────────────────────┐
│  [渐变背景动画]                                          │
│                                                          │
│   ┌────────────────┐   ┌──────────────────────────┐     │
│   │                │   │                          │     │
│   │   [全身照]      │   │  Xiehaoyu-Agent          │     │
│   │                │   │  个人智能体 · 数据问答    │     │
│   │  谢浩宇         │   │                          │     │
│   │  数据科学       │   │  [🔒 请输入访问码]        │     │
│   │  吉首大学       │   │                          │     │
│   │                │   │  [    进入工作台    ]      │     │
│   │                │   │                          │     │
│   │                │   │  查看个人主页 →            │     │
│   └────────────────┘   └──────────────────────────┘     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 3. 侧边栏 — `ChatSidebar.vue`

采用方案 C 的侧边栏信息卡设计，新增个人主页入口：

```
┌──────────────────────────┐
│  [📷]  Xiehaoyu-Agent    │
│       个人智能体工作台     │
│ ──────────────────────── │
│                          │
│  个人信息                 │
│  ┌────────────────────┐  │
│  │ [📷证件照] 谢浩宇    │  │
│  │ 数据科学·吉首大学   │  │
│  │ 📍 广州/深圳        │  │
│  │ 🔍 找实习中         │  │
│  │ [查看完整主页 →]    │  │
│  └────────────────────┘  │
│                          │
│  会话状态                 │
│  [3 消息] [5 步骤] [●]  │
│                          │
│  操作                    │
│  [🗑 清空对话]            │
│  [👤 个人主页]            │
│                          │
│ ──────────────────────── │
│  LangGraph DeepSeek ...  │
│  [退出登录]              │
└──────────────────────────┘
```

### 4. 欢迎卡片 — `WelcomeCard.vue`

采用方案 C 的欢迎卡片设计，展示生活照：

```
┌──────────────────────────────────────────────┐
│                                              │
│  ┌──────┐                                   │
│  │      │  你好，我是谢浩宇                   │
│  │ 生活照│  Xiehaoyu-Agent · 数字分身         │
│  │      │                                   │
│  └──────┘  数据科学与大数据技术 · 吉首大学     │
│            正在找数据分析/数据工程方向实习      │
│                                              │
│  ┌──────────────────────────────────────┐   │
│  │ 🌐 自我介绍——了解我的背景和经历       > │   │
│  │ 📊 数据分析——查询 Olist 电商数据      > │   │
│  │ 📁 项目经历——了解我做过什么项目        > │   │
│  └──────────────────────────────────────┘   │
│                                              │
└──────────────────────────────────────────────┘
```

### 5. 聊天消息 — `ChatMessage.vue`

AI 头像替换为证件照（方案 A），增加"真人"对话感。

### 6. 个人主页 — `ProfileView.vue`

同方案 D，使用 `profile.ts` 中的数据渲染。

### 7. Favicon（可选）

将 `public/favicon.svg` 替换为基于证件照生成的 favicon，让浏览器标签页也体现个人品牌。

## 图片素材分配

| 照片 | 使用位置 | 显示尺寸 | 形状 |
|------|----------|----------|------|
| 证件照.jpg | 聊天头像、侧边栏信息卡、favicon | 34-48px | 圆形 |
| 生活照.jpg | 欢迎卡片、个人主页 Hero | 80-160px | 圆形 |
| 全身照.jpg | 登录页左侧 | 280×380px | 圆角矩形/手机端圆形 |

## 图片优化流程

```bash
# 1. 复制并重命名
cp frontend/照片/证件照.jpg frontend/src/assets/avatar.jpg
cp frontend/照片/生活照.jpg frontend/src/assets/lifestyle.jpg
cp frontend/照片/全身照.jpg frontend/src/assets/fullbody.jpg

# 2. 压缩优化（推荐使用 sharp 或在线工具）
# 目标大小：
#   avatar.jpg    → 20-30KB  (200×200)
#   lifestyle.jpg → 50-80KB  (400×400)
#   fullbody.jpg  → 80-120KB (600×800)

# 3. 可选：生成 WebP 版本
# 在 <img> 中使用 <source srcset="...webp" type="image/webp"> 渐进增强
```

## 组件复用关系

```
profile.ts (数据源)
    │
    ├── LoginView.vue       → import { profile } from '@/data/profile'
    ├── ChatSidebar.vue     → import { profile } from '@/data/profile'
    ├── WelcomeCard.vue     → import { profile } from '@/data/profile'
    ├── ChatMessage.vue     → import { profile } from '@/data/profile'  (仅头像)
    └── ProfileView.vue     → import { profile } from '@/data/profile'
```

所有组件从同一个 `profile.ts` 读取数据，确保信息一致。

## 优点

- 完整的个人品牌形象系统
- 每个页面都有个人形象露出，品牌感最强
- 数据集中管理（`profile.ts`），修改一处全局生效
- 包含独立的在线简历页，可直接分享给 HR

## 缺点

- 改动最大，需要仔细测试
- 个人信息硬编码在前端代码中（但已集中管理）

## 实施建议

按以下顺序逐步实施，每步可独立验证：

```
Step 1: 创建 profile.ts + 图片准备             (30min)
Step 2: 方案 A — ChatMessage 头像替换          (20min)
Step 3: 方案 C — WelcomeCard + Sidebar 升级    (1h)
Step 4: 方案 B — LoginView 左右分栏            (1h)
Step 5: 方案 D — ProfileView 个人主页          (1h)
Step 6: 整体测试、响应式适配、图片优化          (1h)
```

每个 Step 完成后均可独立验证效果，降低风险。