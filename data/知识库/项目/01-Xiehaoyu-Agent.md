# Xiehaoyu-Agent · 具有数据能力的个人智能体

## 关键信息
- 项目类型：LLM Agent 系统 / 全栈应用
- 时间：2026年07月
- 角色：独立设计开发
- 技术栈：Python / LangGraph / DeepSeek / ChromaDB / SQLite / Plotly / FastAPI / Vue 3 / TypeScript / Naive UI / Nginx
- 项目链接：https://gitee.com/xiehaoyu12138/xiehaoyu-agent/tree/main/

## 背景 (Situation)

在准备 2026 秋招（数据分析/数据工程方向）的过程中，我意识到传统简历很难充分展示技术能力。面试官看到的是静态文字，无法直观感受我的数据分析思维和工程能力。同时，面试中经常被问到"介绍一下你自己""你做过什么项目"等问题，回答质量直接影响面试结果。

我希望打造一个能代表我、能展示我数据能力的"数字分身"：
- 能回答关于我的背景、经历、项目的问题
- 能现场演示数据分析能力（自然语言查数据、自动可视化）
- 能给面试官留下深刻印象

## 任务 (Task)

设计并实现一个基于 LLM Agent 的个人智能体与 ChatBI 系统，具备以下核心功能：

1. **个人知识库检索**：RAG 方式检索我的简历、项目、技能，以第一人称回答面试官问题
2. **自然语言查数据**：Text2SQL 引擎，对接真实电商数据集，支持复杂查询
3. **自动可视化**：根据查询结果自动选择图表类型并生成
4. **结果解读**：LLM 自动生成数据洞察和业务建议
5. **生产级部署**：前后端分离架构，公网可访问，带鉴权和限流

## 行动 (Action)

### 1. 架构设计

采用 **LangGraph 状态机**驱动多 Tool 编排：

```
START → planner → tool_router → introduce_me/query_data/visualize/explain_result
                    ↑                    │
                    └──── 循环（≤5步）────┘
                    │
                    └──→ finalize → END
```

- **planner**：LLM 决策节点，输出 JSON `{action, tool, args}` 或 `{action: "finalize", answer}`
- **tool_router**：条件路由，根据 planner 输出分发到具体工具
- **4 个 Tool 节点**：introduce_me（RAG检索）、query_data（Text2SQL）、visualize（自动可视化）、explain_result（结果解读）

### 2. RAG 个人知识库

- **文档切片**：按 Markdown H1/H2/H3 标题切分，超长文本硬切（800字+80字重叠）
- **嵌入模型**：BAAI/bge-large-zh-v1.5（本地运行，1.3GB）
- **向量库**：ChromaDB（cosine 距离，本地持久化）
- **检索策略**：top-k=10，结合 heading 路径提升上下文质量

### 3. Text2SQL 引擎

- **数据集**：Kaggle Olist 巴西电商数据（9 张表，99,441 条订单）
- **Prompt 工程**：完整 schema 描述 + 5 组 few-shot 示例
- **安全校验**：sqlparse 语法解析 + 黑名单（仅允许 SELECT）
- **失败重试**：最多 3 轮，带错误反馈给 LLM 自动修正

### 4. 自动可视化

**智能选图规则**（按优先级）：
1. 1 行 1 列数值 → 指标卡
2. 时间序列 → 折线图
3. 分类 + 数值（≤30 类）→ 柱状图
4. 两个数值列 → 散点图
5. 兜底 → 表格

- 时间列识别：`dtype=datetime` 或列名含 date/time/month 等关键词
- 图表库：Plotly（Python 生成 JSON → 前端 plotly.js 渲染）

### 5. 前后端架构

**后端（FastAPI）**：
- SSE 流式推送：`astream()` 逐节点产出事件
- JWT 鉴权：访问码 → Token，sessionStorage 存储
- 限流：内存级，每小时 50 次配额

**前端（Vue 3 + TypeScript）**：
- UI 框架：Naive UI（暗色主题）
- 动画：Lottie（6 种角色状态：idle/thinking/answering/presenting/error/welcome）
- Markdown 渲染：markdown-it + highlight.js
- 响应式：桌面端侧边栏 + 移动端浮层

### 6. 部署

- **服务器**：腾讯云轻量服务器（2C4G）
- **反向代理**：Nginx（`proxy_buffering off` 保证 SSE 实时推送）
- **进程守护**：systemd 服务
- **一键部署脚本**：`deploy/deploy.sh`（含 HTTPS 自动配置）

## 结果 (Result)

### 量化成果

| 指标 | 数值 |
|------|------|
| 开发周期 | 9 天（2026-07-21 至 2026-07-25 MVP） |
| 代码行数 | 约 5000+ 行（Python + TypeScript） |
| 技术栈数量 | 15+ 种 |
| Text2SQL 支持表数 | 9 张关联表 |
| 数据集规模 | 99,441 条订单 |
| RAG 检索延迟 | < 500ms |
| SSE 流式节点 | 平均 3-5 个事件/请求 |

### 核心功能

1. ** introduce_me**：回答关于我的背景、项目、技能的问题，带来源引用
2. **query_data**：自然语言查询 Olist 数据，支持多表 JOIN、聚合、时间过滤
3. **visualize**：自动生成 5 种图表类型，支持暗色主题
4. **explain_result**：自动生成 1-2 条中文业务洞察

### 技术亮点

- **Agent 自主编排**：LLM 自主决策调用链，最多 5 轮循环推理
- **零成本部署**：DeepSeek API（免费额度）+ ChromaDB 本地 + SQLite 本地
- **生产级体验**：SSE 流式推送、JWT 鉴权、限流、响应式 UI、Lottie 动画
- **可扩展架构**：新增 Tool 只需实现函数 + 注册到 graph，无需改动核心逻辑

### 项目影响

- 作为简历核心项目，直观展示数据工程和全栈开发能力
- 面试官可直接与 Agent 对话，体验我的"数字分身"
- GitHub/Gitee 开源，附在简历中体现工程化和文档能力

## 面试话术

这个项目是我独立设计实现的 Xiehaoyu-Agent，是一个基于 LLM Agent 的个人智能体与 ChatBI 系统。

**背景**是我在准备 2026 秋招时发现传统简历很难展示技术能力，于是想做一个"数字分身"，既能回答关于我的问题，又能现场演示数据分析能力。

**技术架构**上，我用 LangGraph 做了状态机驱动多 Tool 编排，4 个 Tool 分别是：RAG 检索、Text2SQL 查数据、自动可视化、结果解读。LLM 自己决定调用链，最多支持 5 轮推理。

**RAG 模块**，我用 BGE 中文嵌入模型 + ChromaDB 构建了个人知识库，支持检索关于我的简历、项目、技能信息。

**Text2SQL 模块**，我对接了 Kaggle Olist 电商数据集，9 张表 10 万条订单，用完整 schema + few-shot + 语法校验 + 失败重试四层保障保证准确率。

**可视化模块**，我设计了智能选图规则，根据数据特征自动选择指标卡、折线图、柱状图、散点图或表格。

**前后端**，后端用 FastAPI + SSE 流式推送，前端用 Vue 3 + Naive UI 暗色主题，还有 6 种 Lottie 动画角色状态。

**部署**在腾讯云轻量服务器，Nginx 反向代理，systemd 守护，带 JWT 鉴权和限流。

整个项目 9 天完成，5000+ 行代码，15+ 种技术栈，现在已经作为我的简历项目开源在 Gitee 上。
