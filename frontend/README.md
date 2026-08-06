# frontend/ — Vue 3 + TypeScript 前端

两个页面：作品集主页 `/`（个人展示）和全屏聊天页 `/chat`（与 Agent 对话）。深/浅色主题切换，SSE 实时接收 Agent 执行过程，Plotly 渲染图表，Lottie 角色动画。

技术栈：Vue 3 + TypeScript + Vite + Naive UI + Pinia + vue-router + markdown-it + highlight.js + plotly.js-dist + lottie-web。

## 快速开始

```bash
npm install
npm run dev       # 开发服务器 http://localhost:5173，/api 代理到 127.0.0.1:8000
npm run build     # vue-tsc 类型检查 + 产物输出到 dist/
npm run preview   # 预览构建产物
```

## 目录结构

```
src/
├── main.ts                 # 入口（Pinia + Router）
├── App.vue                 # 根组件（Naive UI 主题配置）
├── router/index.ts         # / → PortfolioView，/chat → ChatView，其余重定向 /
├── stores/chat.ts          # 聊天状态机 + SSE 调度 + Lottie 动画状态
├── data/profile.ts         # 作品集静态文案（关于/经历/项目，改文案只动这里）
├── utils/
│   ├── sse.ts              # SSE 客户端（fetch + ReadableStream 逐行解析）
│   ├── markdown.ts         # markdown-it + highlight.js 渲染
│   ├── artifact.ts         # 从 trace 中倒序查找最新 artifact
│   ├── quick-questions.ts  # 欢迎屏快捷提问 chips 配置
│   └── tool-constants.ts   # 工具中文标签 / 颜色 / 图表类型映射
├── composables/
│   ├── useTheme.ts         # 深/浅色切换（localStorage 持久化）
│   ├── useScrollSpy.ts     # 滚动锚点高亮跟随
│   ├── useRevealOnScroll.ts # 滚动出现动画
│   └── useMediaQuery.ts    # 响应式断点
├── styles/global.css       # CSS 变量主题体系（全站颜色唯一事实源）
├── assets/lottie/          # 6 个状态的 Lottie JSON
├── views/
│   ├── PortfolioView.vue   # 作品集主页
│   └── ChatView.vue        # 全屏聊天页
└── components/
    ├── portfolio/          # SiteSidebar / AboutSection / ExperienceSection /
    │                       # ProjectsSection / ChatSection / SiteFooter /
    │                       # SectionHeading / MouseSpotlight
    ├── chat/               # ChatWidget / ChatMessage / MessageBubble /
    │                       # InlineResult / WelcomeScreen / ChatInput
    ├── shared/AnimatedAvatar.vue   # Lottie 角色动画容器
    └── result/ChartRenderer.vue    # Plotly 图表渲染
```

Naive UI 组件和常用 API 通过 unplugin-auto-import / unplugin-vue-components 自动导入（类型声明见 `src/auto-imports.d.ts`、`src/components.d.ts`，均为构建生成，勿手改）。

## 核心机制

### 聊天数据流

```
ChatInput → chat store.send() → sseChatStream() → POST /api/chat
  → planner_decision → 更新 currentTool / 轨迹标签
  → tool_end        → 追加 ToolTrace（含 artifact：df_json / figure_json / citations）
  → final_answer    → 写入 assistant 消息
  → [DONE]          → 收尾，动画回 idle
```

### SSE 客户端（[utils/sse.ts](src/utils/sse.ts)）

- 120 秒超时；网络类错误最多自动重试 3 次（指数退避 1s/2s/4s）。
- 外部 `AbortSignal` 联动"停止生成"：中断后已生成内容保留，可一键重试。
- 解析失败的单行只警告不崩溃（容忍畸形 JSON）。

### 结果展示

每条 assistant 消息内联展示自己的图表（ChartRenderer ← `figure_json`）、数据表（← `df_json`，SQL 默认折叠）和执行轨迹时间线（颜色编码：蓝=查询 / 绿=图表 / 橙=检索 / 紫=解读）。

### 主题系统

CSS 变量驱动（[global.css](src/styles/global.css) 定义变量），`useTheme` 切换并持久化到 localStorage，Naive UI 同步切换 `darkTheme` / `lightTheme`。深色主色调 `#64ffda`，浅色 `#0969da`。新增颜色一律走 CSS 变量，不要硬编码。

### Lottie 角色动画

6 种状态：`idle` / `welcome` / `thinking` / `answering` / `presenting` / `error`。状态管理内置在 [stores/chat.ts](src/stores/chat.ts)（不单独抽 composable），由 [AnimatedAvatar.vue](src/components/shared/AnimatedAvatar.vue) 渲染。

## 响应式

桌面端（>980px）左栏固定导航 + 右栏内容；移动端（≤980px）顶部身份块 + 横向导航。断点判断统一走 `useMediaQuery`。

## 改内容去哪改

| 要改什么 | 改哪里 |
| --- | --- |
| 作品集文案（关于/经历/项目） | [src/data/profile.ts](src/data/profile.ts) |
| 欢迎屏快捷提问 | [src/utils/quick-questions.ts](src/utils/quick-questions.ts) |
| 工具显示名 / 颜色 | [src/utils/tool-constants.ts](src/utils/tool-constants.ts) |
| 主题颜色 | [src/styles/global.css](src/styles/global.css) 的 CSS 变量 |
