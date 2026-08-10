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
├── stores/sessions.ts      # 会话列表/创建/重命名/删除/回放（X-User-Id 注入）
├── data/profile.ts         # 作品集静态文案（关于/经历/项目，改文案只动这里）
├── utils/
│   ├── sse.ts              # SSE 客户端（fetch + ReadableStream 逐行解析 + 错误分类重试）
│   ├── markdown.ts         # markdown-it + highlight.js（核心库按需注册 6 种语言）渲染
│   ├── artifact.ts         # 从 trace 中倒序查找最新 artifact
│   ├── user.ts             # 匿名用户 ID（localStorage UUID v4）
│   ├── time.ts             # 相对时间格式化
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
    │                       # InlineResult / WelcomeScreen / ChatInput / SessionSidebar
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

- 180 秒超时（覆盖后端多步 LLM + SQL 重试的最坏合法时长，Nginx `proxy_read_timeout` 300s 之内）。
- 错误分类重试（`SSEStreamError.kind`）：只有**连接未建立**（`connect`）才自动重试（最多 3 次，指数退避 1s/2s/4s）；流中途断开（`stream`）与超时（`timeout`）**不重试**——后端可能已执行完部分步骤，重试会双倍消耗 LLM 额度；429 等应用层错误立即透传。`onError` 回调携带 HTTP 状态码，429 限流直接展示后端友好文案、不加「执行失败：」前缀（08-09 方案 T4-3）。
- 外部 `AbortSignal` 联动"停止生成"：中断后已生成内容保留，可一键重试；重试成对删除 user+assistant 消息再重发（regenerate 语义，T4-2）；超时与手动停止分别提示（不再混淆为"已取消"）。
- 解析失败的单行只警告不崩溃（容忍畸形 JSON）。

### 结果展示

每条 assistant 消息内联展示自己的图表（ChartRenderer ← `figure_json`）、数据表（← `df_json`，SQL 默认折叠）和执行轨迹时间线（颜色编码：蓝=查询 / 绿=图表 / 橙=检索 / 紫=解读）。RAG 回答附「引用来源」折叠区（source + heading 路径 + 相似度，T4-1）；图表区底部小字标注「演示数据来自 Kaggle Olist 公开数据集」（T4-4）。

### 会话切换与等待提示（08-09 方案 T3 / T4-10）

- 流式期间点击侧栏会话或「新会话」：先 `confirm` 提示将中断本次回答，确认后 `stopStreaming()` 中断当前流再切换（参考 CopilotKit 切换 thread 自动 abortRun）。
- 流式超过 60s 在消息区底部显示「仍在处理中，请耐心等待…」中间态（`chat.slowStream`）；超时文案为「响应时间较长，请稍后重试」。

### 转化出口（T4-7）

聊天页顶栏右侧：「联系我」弹层（邮箱/微信，点击即复制）+「下载简历」按钮（`/resume.pdf`，静态资产在 `public/resume.pdf`，替换文件即可换版）。

### 主题系统

CSS 变量驱动（[global.css](src/styles/global.css) 定义变量），`useTheme` 切换并持久化到 localStorage；首次访问无本地偏好时跟随系统 `prefers-color-scheme`（T4-9）。Naive UI 同步切换 `darkTheme` / `lightTheme`。深色主色调 `#64ffda`，浅色 `#0969da`。新增颜色一律走 CSS 变量，不要硬编码（错误气泡三色：`--error-bg/-border/-text`，T4-6）。

### Lottie 角色动画

6 种状态：`idle` / `welcome` / `thinking` / `answering` / `presenting` / `error`。状态管理内置在 [stores/chat.ts](src/stores/chat.ts)（不单独抽 composable），由 [AnimatedAvatar.vue](src/components/shared/AnimatedAvatar.vue) 渲染。

## 响应式

桌面端（>980px）左栏固定导航 + 右栏内容；移动端（≤980px）顶部身份块 + 横向导航。断点判断统一走 `useMediaQuery`。聊天页侧栏为 desktop docked / 移动端（≤767px）overlay 抽屉双模式：默认收起，打开时带遮罩、点击外部收起（T4-8，参考 CopilotKit sidebar）。

## 改内容去哪改

| 要改什么 | 改哪里 |
| --- | --- |
| 作品集文案（关于/经历/项目） | [src/data/profile.ts](src/data/profile.ts) |
| 欢迎屏快捷提问 | [src/utils/quick-questions.ts](src/utils/quick-questions.ts) |
| 工具显示名 / 颜色 | [src/utils/tool-constants.ts](src/utils/tool-constants.ts) |
| 主题颜色 | [src/styles/global.css](src/styles/global.css) 的 CSS 变量 |
