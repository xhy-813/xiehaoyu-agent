# 方案 D：独立个人主页

> **工时**：~3h | **改动文件**：5+ 个 | **难度**：★★★☆☆

## 概述

新增一个独立的个人主页路由 `/profile`，集中展示你的照片、教育背景、技能、项目经历和联系方式。这相当于一个"在线简历 + 个人形象页"，适合发送给 HR 或面试官。

## 新增内容

### 1. 新增路由 — `router/index.ts`

```ts
{
  path: '/profile',
  name: 'Profile',
  component: () => import('@/views/ProfileView.vue'),
  meta: { requiresAuth: false },  // 无需登录即可访问
},
```

### 2. 新增个人主页 — `views/ProfileView.vue`

**页面结构**：

```
┌──────────────────────────────────────────────────────┐
│  [← 返回]                              Xiehaoyu-Agent │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │                                                │  │
│  │         ┌──────────┐                           │  │
│  │         │          │                           │  │
│  │         │ 生活照    │   谢浩宇                   │  │
│  │         │          │   数据科学与大数据技术       │  │
│  │         │  (圆形)   │   吉首大学 · 2023 级本科    │  │
│  │         │          │   📍 广州 / 深圳            │  │
│  │         └──────────┘                           │  │
│  │                                                │  │
│  │         [🔗 GitHub] [📧 Email] [📱 微信]       │  │
│  │                                                │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │ 💻 技术栈     │ │ 🎓 教育背景  │ │ 🏢 实习经历  │  │
│  │              │ │              │ │              │  │
│  │ Python       │ │ 吉首大学     │ │ 龙腾出行     │  │
│  │ SQL          │ │ 数据科学    │ │ 数据工程实习 │  │
│  │ Pandas       │ │ 2023-2027   │ │ 2025.03-     │  │
│  │ Scrapy       │ │ GPA 3.x     │ │ 2025.09      │  │
│  │ Tableau      │ │              │ │              │  │
│  │ Hive/Spark   │ │              │ │              │  │
│  │ Docker       │ │              │ │              │  │
│  │ ...          │ │              │ │              │  │
│  └──────────────┘ └──────────────┘ └──────────────┘  │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │ 🚀 项目经历                                    │  │
│  │                                                │  │
│  │  K12 数仓与 PowerBI 可视化看板                   │  │
│  │  Hive 数仓分层 + ETL + PowerBI 可视化            │  │
│  │                                                │  │
│  │  郑州机场知识库系统                              │  │
│  │  RAG + 知识图谱 + 智能问答                       │  │
│  │                                                │  │
│  │  Xiehaoyu-Agent（本项目）                       │  │
│  │  LangGraph Agent + ChatBI + 个人数字分身         │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │ 📞 联系我                                      │  │
│  │ 欢迎交流数据分析、数据工程或实习机会              │  │
│  │ 📧 email@example.com                           │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**核心实现**：

```html
<template>
  <div class="profile-page">
    <!-- 顶部导航 -->
    <div class="profile-nav">
      <n-button text @click="router.back()">
        <template #icon><n-icon><svg>←</svg></n-icon></template>
        返回
      </n-button>
      <span class="nav-brand">Xiehaoyu-Agent</span>
      <n-button text @click="router.push('/login')">
        进入工作台
      </n-button>
    </div>

    <!-- Hero 区域 -->
    <section class="hero-section">
      <div class="hero-avatar">
        <img src="@/assets/lifestyle.jpg" alt="谢浩宇" />
      </div>
      <h1 class="hero-name">谢浩宇</h1>
      <p class="hero-title">数据科学与大数据技术 · 吉首大学 2023 级本科</p>
      <p class="hero-location">📍 广州 / 深圳</p>
      <div class="hero-links">
        <a href="https://github.com/yourname" target="_blank" class="hero-link">
          <n-icon><svg>GitHub</svg></n-icon> GitHub
        </a>
        <a href="mailto:email@example.com" class="hero-link">
          <n-icon><svg>Email</svg></n-icon> Email
        </a>
      </div>
    </section>

    <!-- 卡片区域 -->
    <section class="cards-section">
      <div class="cards-grid">
        <n-card title="💻 技术栈" :bordered="true" class="info-card">
          <div class="skill-tags">
            <span v-for="s in skills" :key="s" class="skill-tag">{{ s }}</span>
          </div>
        </n-card>
        <n-card title="🎓 教育背景" :bordered="true" class="info-card">
          <p><strong>吉首大学</strong></p>
          <p>数据科学与大数据技术</p>
          <p>2023 - 2027 · 本科</p>
        </n-card>
        <n-card title="🏢 实习经历" :bordered="true" class="info-card">
          <p><strong>龙腾出行</strong> · 数据工程实习生</p>
          <p>2025.03 - 2025.09</p>
          <p>POI 匹配、数据管道、LLM 数据清洗</p>
        </n-card>
      </div>
    </section>

    <!-- 项目经历 -->
    <section class="projects-section">
      <h2>🚀 项目经历</h2>
      <div class="project-list">
        <div v-for="p in projects" :key="p.name" class="project-card">
          <h3>{{ p.name }}</h3>
          <p>{{ p.desc }}</p>
          <div class="project-tech">
            <span v-for="t in p.tech" :key="t" class="tech-tag">{{ t }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 联系我 -->
    <section class="contact-section">
      <h2>📞 联系我</h2>
      <p>欢迎交流数据分析、数据工程或实习机会</p>
      <p>📧 email@example.com</p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const skills = ['Python', 'SQL', 'Pandas', 'Scrapy', 'Tableau', 'FineBI', 'Hive', 'Spark', 'Docker', 'Git', 'LLM API', 'LangChain']
const projects = [
  { name: 'K12 数仓与 PowerBI 可视化看板', desc: 'Hive 数仓分层 + ETL + PowerBI 可视化', tech: ['Hive', 'SQL', 'PowerBI'] },
  { name: '郑州机场知识库系统', desc: 'RAG + 知识图谱 + 智能问答', tech: ['Python', 'LangChain', 'ChromaDB'] },
  { name: 'Xiehaoyu-Agent', desc: 'LangGraph Agent + ChatBI + 个人数字分身', tech: ['LangGraph', 'DeepSeek', 'Vue 3'] },
]
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: #0a0a0f;
  color: #e0e0e0;
}

.profile-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.nav-brand {
  font-weight: 700;
  background: linear-gradient(135deg, #63e2b7, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* Hero */
.hero-section {
  text-align: center;
  padding: 3rem 1.5rem 2rem;
}

.hero-avatar {
  width: 160px;
  height: 160px;
  border-radius: 50%;
  overflow: hidden;
  margin: 0 auto 1.5rem;
  border: 3px solid rgba(99, 226, 183, 0.3);
  box-shadow: 0 0 40px rgba(99, 226, 183, 0.1);
}

.hero-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hero-name {
  font-size: 2rem;
  font-weight: 800;
  margin: 0 0 0.5rem;
}

.hero-title {
  font-size: 1rem;
  color: #888;
  margin: 0 0 0.25rem;
}

.hero-location {
  font-size: 0.9rem;
  color: #63e2b7;
  margin: 0 0 1rem;
}

.hero-links {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.hero-link {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  color: #ccc;
  text-decoration: none;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.hero-link:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #63e2b7;
}

/* Cards grid */
.cards-section {
  padding: 0 2rem 2rem;
  max-width: 1100px;
  margin: 0 auto;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

@media (max-width: 768px) {
  .cards-grid {
    grid-template-columns: 1fr;
  }
}

.info-card {
  background: rgba(24, 24, 30, 0.85) !important;
}

.skill-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.skill-tag {
  font-size: 0.75rem;
  padding: 0.2rem 0.6rem;
  border-radius: 100px;
  background: rgba(99, 226, 183, 0.1);
  color: #63e2b7;
  border: 1px solid rgba(99, 226, 183, 0.15);
}

/* Projects */
.projects-section {
  padding: 0 2rem 2rem;
  max-width: 1100px;
  margin: 0 auto;
}

.project-list {
  display: grid;
  gap: 1rem;
}

.project-card {
  padding: 1.25rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
}

.project-card h3 {
  margin: 0 0 0.5rem;
  font-size: 1rem;
  color: #e0e0e0;
}

.project-card p {
  margin: 0 0 0.75rem;
  font-size: 0.85rem;
  color: #888;
}

.project-tech {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.tech-tag {
  font-size: 0.7rem;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  background: rgba(129, 140, 248, 0.1);
  color: #818cf8;
}

/* Contact */
.contact-section {
  text-align: center;
  padding: 2rem;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.contact-section h2 {
  font-size: 1.2rem;
  margin: 0 0 0.5rem;
}

.contact-section p {
  color: #888;
  font-size: 0.88rem;
  margin: 0.25rem 0;
}
</style>
```

### 3. 入口设置

**侧边栏增加入口** — `ChatSidebar.vue`：

```html
<!-- 在操作区新增按钮 -->
<n-button block secondary size="small" @click="router.push('/profile')">
  <template #icon><n-icon>👤</n-icon></template>
  个人主页
</n-button>
```

**登录页增加入口** — `LoginView.vue`：

```html
<!-- 在登录卡片底部新增链接 -->
<p class="login-footer">
  如需访问码，请联系：谢浩宇 ·
  <router-link to="/profile" class="profile-link">查看个人主页</router-link>
</p>
```

### 4. 图片准备

```bash
cp frontend/照片/生活照.jpg frontend/src/assets/lifestyle.jpg
```

### 5. 个人信息配置文件（推荐）— `src/data/profile.ts`

```ts
// 将个人信息集中管理，方便后续维护
export const profile = {
  name: '谢浩宇',
  title: '数据科学与大数据技术',
  school: '吉首大学',
  grade: '2023 级本科',
  location: '广州 / 深圳',
  email: 'email@example.com',
  github: 'https://github.com/yourname',
  status: '正在找数据分析 / 数据工程方向实习',
  skills: ['Python', 'SQL', 'Pandas', 'Scrapy', 'Tableau', 'FineBI', 'Hive', 'Spark', 'Docker', 'Git', 'LLM API', 'LangChain'],
  projects: [
    { name: 'K12 数仓与 PowerBI 可视化看板', desc: '...', tech: ['Hive', 'SQL', 'PowerBI'] },
    // ...
  ],
  experience: [
    { company: '龙腾出行', role: '数据工程实习生', period: '2025.03 - 2025.09', desc: '...' },
  ],
}
```

## 优点

- 完整的个人形象展示，适合发给 HR
- 无需登录即可访问（`requiresAuth: false`）
- 个人信息集中管理，维护方便
- 可作为在线简历独立使用

## 缺点

- 新增页面和路由，改动较大
- 需要和维护中的个人信息保持同步
- 如果信息不完整，页面会显得空

## 扩展建议

- 路由设为 `meta: { requiresAuth: false }`，方便分享给外部人员
- 可添加简历 PDF 下载按钮
- 可添加访问统计（如百度统计），了解哪些 HR 看过你的页面