# Xiehaoyu-Agent 项目概述

## 标签

#项目 #Xiehaoyu-Agent #LLM #Agent #ChatBI #RAG #简历项目

## 项目概述

Xiehaoyu-Agent 是一个代表本人的对外 LLM Agent，兼具两大能力：

1. **介绍本人**：基于 RAG 检索个人知识库（简历、项目、实习经历），回答面试官/HR 关于"我是谁、做过什么"的问题。
2. **ChatBI（自然语言查数据）**：面向 Olist 巴西电商数据集，支持 Text2SQL、SQL 自动纠错重试、结果自动可视化、结果自然语言解读。

面试官可通过公网链接 + 访问码直接体验，作为简历上的差异化亮点项目。

## 项目定位

- **目标岗位**：数据方向实习/秋招（数据分析、数据工程、数据科学）
- **核心卖点**：把"自我介绍"和"数据分析能力"融进一个能跑的 Agent 产品，让面试官在见到你之前就能与你的 Agent 对话
- **完成度目标**：MVP 优先（1~2 周），后续迭代
- **成本约束**：零成本（免费云 + 免费 LLM 额度）

## 技术栈

| 层         | 选型                                                   | 备注                                                 |
| ---------- | ------------------------------------------------------ | ---------------------------------------------------- |
| LLM        | DeepSeek Chat API (`deepseek-v4-flash`)                | 中文效果好、便宜、有免费额度；可切千问               |
| Agent 编排 | LangGraph 1.2.9+                                       | 状态机式，简历含金量高；支持 `astream()` 流式        |
| 后端       | FastAPI + Uvicorn                                      | 原生 async，SSE 流式推送，JWT 鉴权                   |
| 前端       | Vue 3 + TypeScript + Vite + Naive UI                   | 暗色主题，SSE 实时接收，Plotly 图表渲染               |
| RAG 向量库 | ChromaDB（本地持久化）                                 | 零成本，cosine 距离                                  |
| Embedding  | BAAI/bge-large-zh-v1.5                                 | 通过 sentence-transformers 本地跑                    |
| 数据仓库   | SQLite（本地 .db 文件）                                | 部署简单，够 demo                                    |
| 数据集     | Kaggle Olist 巴西电商                                  | 9 张表关联，字段清晰                                 |
| 可视化     | Plotly（Python 生成 JSON → 前端 plotly.js 渲染）      | 交互式，零丢失                                       |
| Web UI     | Streamlit（原版）/ Vue 3 + FastAPI（新版）             | 新版支持 SSE 流式、暗色主题、响应式布局               |
| 部署       | 腾讯云轻量服务器 (2C4G) / HuggingFace Spaces           | Nginx 反向代理 + systemd 守护                        |
| 鉴权/限流  | 访问码 → JWT + 内存限流（每小时配额）                  | 防刷 API                                             |
| 代码托管   | GitHub（公开仓）                                       | 简历附链接                                           |

## 架构

### 总览

```
用户浏览器 (Vue 3 / Streamlit)
    │
    │ POST /api/chat (SSE 流式) 或 streamlit run
    ▼
FastAPI 后端 (JWT 鉴权 + 限流)  /  Streamlit 直连
    │
    ▼
┌────────────────────────────────────────┐
│    Agent Orchestrator (LangGraph)      │
│                                        │
│   ┌────────────────────────────────┐   │
│   │      LLM Planner (DeepSeek)    │   │
│   └───────────────┬────────────────┘   │
│                   │ 选择 Tool           │
│    ┌──────────────┼─────────────┐      │
│    ▼              ▼             ▼      │
│ introduce_me  query_data   visualize   │
│    (RAG)      (Text2SQL)   (Plotly)    │
│                                        │
│                   ▼                    │
│           explain_result               │
│                                        │
│   循环直到 LLM 输出 final_answer         │
│   (max 5 步，可配置)                    │
└────────────────────────────────────────┘
    │           │            │
    ▼           ▼            ▼
Chroma      SQLite       Plotly
个人知识库    电商数据      图表 JSON
```

### 流式推送 (SSE)

新版 Vue 3 + FastAPI 架构使用 Server-Sent Events 实现实时流式推送：

```
前端 fetch POST /api/chat
  → 后端 stream_run() → app.astream()
    → 每个节点产出 yield 事件:
      - planner_decision: LLM 决策信息
      - tool_end: 工具执行结果（含序列化的 DataFrame/Plotly Figure JSON）
      - final_answer: 最终回答
    → data: [DONE] 结束
```

- `_serialize_artifact()`: DataFrame → `df_json` + `df_shape` + `df_columns`, Plotly Figure → `figure_json`
- Nginx 需配置 `proxy_buffering off` 保证 SSE 实时推送

### 状态机（LangGraph）

节点：

- `planner`：调用 LLM，输入历史消息 + tool 结果，输出下一步动作（调用哪个 tool，或结束）
- `tool_router`：根据 planner 输出分发到具体 tool 节点
- `introduce_me` / `query_data` / `visualize` / `explain_result`：4 个 tool 节点
- `finalize`：拼装最终回答返回用户

边：

- START → planner → tool_router → 各 tool → planner（循环，最多 5 轮防死循环）
- planner → finalize → END（当 LLM 判断已足够回答）

### Tool 详细设计

#### Tool 1: `introduce_me(question: str)`

- 输入：关于本人的问题
- 流程：
  1. 用 BGE-large-zh 嵌入 question
  2. Chroma 向量检索 top-5 相关文档片段
  3. 构造 RAG prompt：`system(人设) + retrieved_chunks + question`
  4. LLM 生成回答
- 输出：回答文本 + 引用来源（文件路径 + heading + score）
- 语料来源：`career/`、`school/`、`work/`、`projects/`、`tech/`、`life/`、`methods/`、`templates/` 下所有 md
- 切片策略：按 markdown H1/H2/H3 切，或 800 字硬切 + overlap 80

#### Tool 2: `query_data(question: str)`

- 输入：自然语言数据问题
- 流程（Text2SQL 工程化）：
  1. **完整 Schema Prompt**：把 9 张表完整 schema 描述 + 5 个 few-shot 示例一起给 LLM（未做 schema linking 筛选，数据量不大时全量给效果更好）
  2. LLM 生成 SQL
  3. **SQL 校验**：sqlparse 语法检查 + 只允许 SELECT（防注入）
  4. 执行 SQL
  5. **失败重试**：若报错，把错误信息 + 原 SQL 反馈给 LLM 重写，最多 3 轮
- 输出：`QueryResult` 含 SQL 字符串 + 结果 DataFrame + 执行耗时 + 重试次数 + trace

#### Tool 3: `visualize(df: DataFrame, question: str)`

- 输入：查询结果 + 用户问题
- 自动选图规则（按优先级）：
  1. 1 行 1 列数值 → 大数字指标卡 (Indicator)
  2. 时间序列（1 时间列 + 1~N 数值列）→ 折线图
  3. 分类 + 数值（分类数 ≤ 30）→ 柱状图（按数值降序）
  4. 两个数值列 → 散点图
  5. 兜底 → 表格
- 输出：`VizResult` 含 Plotly Figure + chart_type + reason

#### Tool 4: `explain_result(df, sql, question)`

- LLM 用自然语言解读结果，给出 1~2 条中文业务洞察
- 输出：解读文本

### 数据流示例

用户问："olist 里 2018 年销量 top 5 的品类是什么？帮我画个图。"

```
planner → query_data → visualize → explain_result → finalize
```

用户问："你之前 K12 数仓项目用了什么技术？"

```
planner → introduce_me → finalize
```

用户问："你了解电商数据吗？给我看一下 olist 的月订单趋势。"

```
planner → introduce_me（回答"了解，我做过 XX"）
       → query_data（月订单）
       → visualize
       → explain_result
       → finalize
```

## 编码规范

### 目录结构

```
Xiehaoyu-Agent/                    # 仓库根目录
├── app.py                         # Streamlit 入口（原版 UI）
├── agent/
│   ├── __init__.py
│   ├── graph.py                   # LangGraph 定义 + stream_run() + _serialize_artifact()
│   ├── planner.py                 # LLM Planner prompt
│   └── tools/
│       ├── introduce_me.py        # RAG 个人知识库检索问答
│       ├── query_data.py          # Text2SQL + 安全校验 + 重试
│       ├── visualize.py           # 自动可视化（5 种图表类型）
│       └── explain_result.py      # LLM 结果解读
├── backend/
│   ├── requirements.txt           # fastapi, uvicorn, PyJWT
│   └── app/
│       ├── main.py                # FastAPI 入口 (CORS, 路由)
│       ├── dependencies.py        # JWT 验证 Depends
│       ├── routers/
│       │   ├── auth.py            # POST /api/auth/login
│       │   └── chat.py            # POST /api/chat (SSE 流式)
│       ├── schemas/
│       │   ├── auth.py            # LoginRequest, TokenResponse
│       │   └── chat.py            # ChatRequest
│       └── middleware/
│           └── rate_limit.py      # 内存限流
├── frontend/
│   ├── src/
│   │   ├── main.ts                # Vue 入口 (Pinia + Router)
│   │   ├── App.vue                # 根组件 (暗色主题)
│   │   ├── router/index.ts        # /login, /chat 路由守卫
│   │   ├── stores/
│   │   │   ├── auth.ts            # JWT 认证状态
│   │   │   └── chat.ts            # 聊天状态 + SSE 流式
│   │   ├── utils/sse.ts           # SSE 客户端 (fetch + ReadableStream)
│   │   ├── views/
│   │   │   ├── LoginView.vue      # 登录页
│   │   │   └── ChatView.vue       # 主聊天布局
│   │   └── components/
│   │       ├── chat/              # ChatSidebar, ChatMain, ChatMessage, ChatInput, WelcomeCard
│   │       └── result/            # ResultPanel, ResultSummary, ResultData, ResultChart, ResultTrace, ChartRenderer
│   └── vite.config.ts
├── chatbi/
│   ├── schema.py                  # 9 张表结构描述
│   ├── few_shots.py               # 5 组 (问题, SQL) 示例
│   ├── validator.py               # SQL 安全校验 (sqlparse + 黑名单)
│   ├── load_olist.py              # CSV → SQLite 导入脚本
│   └── data/olist.db              # SQLite 数据库
├── rag/
│   ├── ingest.py                  # 语料切片 + 入库脚本 (BGE-large-zh)
│   ├── retriever.py               # top-k 检索封装
│   └── data/chroma/               # Chroma 持久化向量库
├── prompts/
│   ├── system_persona.md          # 核心人设
│   ├── text2sql.md                # Text2SQL 模板
│   └── explain.md                 # 数据解读模板
├── configs/
│   └── settings.py                # API key、模型名、JWT、限流、CORS 参数
├── deploy/
│   ├── deploy.sh                  # 一键部署脚本
│   ├── nginx.conf                 # Nginx 配置 (SPA + API 代理 + SSE 禁用缓冲)
│   └── xiehaoyu-agent.service     # systemd 服务文件
├── docs/
│   ├── Vue3-FastAPI-重构方案.md    # 重构方案设计文档
│   └── superpowers/
│       ├── specs/                 # 设计文档
│       └── plans/                 # 实施计划
├── tests/
│   ├── smoke_agent.py             # Agent 全链路冒烟测试
│   ├── smoke_introduce_me.py      # RAG 工具测试
│   ├── smoke_text2sql.py          # Text2SQL 测试
│   ├── smoke_viz_explain.py       # 可视化+解读测试
│   ├── test_text2sql.py           # Text2SQL 准确率评测
│   └── test_rag.py
├── requirements.txt               # Python 依赖
├── README.md                      # 项目介绍 + 架构图 + 部署说明
└── .env.example                   # DEEPSEEK_API_KEY, ACCESS_CODE, JWT_SECRET, CORS_ORIGINS
```

### 命名约定

- 模块/文件：`snake_case`
- 类：`PascalCase`
- Prompt 文件：`.md` 放 `prompts/`，代码里用 `pathlib` 读
- 环境变量：全大写 `SNAKE_CASE`

### 依赖清单

**根目录 `requirements.txt`**（Agent 核心 + Streamlit）：
```
streamlit>=1.32
langgraph>=0.0.40
langchain-core>=0.1.40
openai>=1.20
chromadb>=0.4.24
sentence-transformers>=2.5
sqlparse>=0.4
sqlalchemy>=2.0
pandas>=2.1
plotly>=5.20
python-dotenv>=1.0
```

**`backend/requirements.txt`**（FastAPI 后端）：
```
fastapi>=0.110
uvicorn[standard]>=0.29
PyJWT>=2.8
```

**前端 `package.json`**（Vue 3 + Naive UI）：
```
vue 3.5+, vite 8+, typescript, naive-ui, pinia, vue-router 4,
markdown-it, highlight.js, plotly.js-dist, @heroicons/vue
```

## 实施计划（MVP，1~2 周）

按天分解，每天可交付、可验证。

### Day 1：环境 & 数据准备

- [x] 建 GitHub 仓，初始化 README、.gitignore
- [x] 建 Python venv，安装 requirements
- [x] Kaggle 下载 [Olist 数据集](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- [x] 写脚本把 9 个 CSV 导入 `chatbi/data/olist.db`（SQLite）
- [x] 在 SQLite 里补充表关系注释，导出 schema 描述到 `chatbi/schema.py`

- **验收**：`sqlite3 olist.db "select count(*) from orders"` 能出结果 ✅ 99441 行

### Day 2：Text2SQL Tool（核心）

- [x] 写 `prompts/text2sql.md`：包含 schema、5 个 few-shot、输出格式约束
- [x] 写 `chatbi/validator.py`：sqlparse 校验 + 只允许 SELECT
- [x] 写 `agent/tools/query_data.py`：调 LLM → 校验 → 执行 → 失败重试（最多 3 轮）
- [x] 手写 5 个测试 case 跑通

- **验收**："2018 年每月订单数" 能正确返回 DataFrame ✅ 5/5 通过

### Day 3：Visualize + Explain Tool

- [x] 写 `agent/tools/visualize.py`：根据 df shape/dtype 自动选图（5 种类型）
- [x] 写 `agent/tools/explain_result.py`：LLM 解读结果

- **验收**：给定 df 能画出合适图 + 输出中文解读 ✅ 4/4 通过

### Day 4：RAG（介绍我自己）Tool

- [x] 写 `rag/ingest.py`：扫 8 个顶层目录下 md，按 H1/H2/H3 切片（800 字硬切 + overlap 80）
- [x] 用 BGE-large-zh 嵌入，入 Chroma
- [x] 写 `rag/retriever.py`：top-5 检索封装
- [x] 写 `prompts/system_persona.md`：核心人设 + 边界
- [x] 写 `agent/tools/introduce_me.py`

- **验收**："介绍一下你自己"、"你 K12 项目做了什么" 能给出合理回答且带引用 ✅ 4/4 通过

### Day 5：Agent 编排（LangGraph）

- [x] 写 `agent/planner.py`：让 LLM 输出 JSON `{action, tool, args}` 或 `{action: "finalize", answer}`
- [x] 写 `agent/graph.py`：LangGraph 状态机，节点循环最多 5 步
- [x] 端到端跑通：CLI 输入问题 → 输出答案 + 轨迹

- **验收**：3 类问题（纯介绍、纯查数、混合）都能走通并输出正确 tool 调用序列 ✅ 3/3 通过

### Day 6：Streamlit UI

- [x] `app.py`：登录页（访问码校验）→ 主页
- [x] 主页：左边 chat，右边 3 个 Tab（Data / Chart / Trace）
- [x] 每轮对话展示 agent 轨迹（thought / tool / observation 折叠卡片）
- [x] session 限流：每 session 每小时 50 次

- **验收**：本地 `streamlit run app.py` 完整体验 ✅

### Day 7~8：Vue 3 + FastAPI 重构

- [x] 后端 API 层：FastAPI + SSE 流式推送 + JWT 鉴权 + 限流
- [x] `agent/graph.py` 新增 `stream_run()` 异步生成器 + `_serialize_artifact()` 序列化
- [x] `configs/settings.py` 新增 JWT/CORS 配置项
- [x] 前端核心：Vue 3 + Naive UI 暗色主题 + Pinia 状态管理 + SSE 客户端
- [x] 结果面板：DataTable + SQL 折叠 + Plotly 图表渲染 + 执行轨迹时间线
- [x] 响应式布局：桌面端侧边栏 + 移动端浮层

- **验收**：前后端联调，SSE 流式推送正常，图表渲染完整 ✅

### Day 9：部署配置

- [x] Nginx 配置：SPA 静态文件 + API 反向代理 + `proxy_buffering off`
- [x] systemd 服务文件：uvicorn 守护进程
- [x] 一键部署脚本 `deploy/deploy.sh`
- [x] `.env.example` 更新：新增 JWT_SECRET, CORS_ORIGINS 等配置项

- **验收**：部署配置完整，可在服务器上一键部署 ✅

### Day 10：评测 & 打磨

- [ ] 写 `tests/test_text2sql.py`：50 道题（简单 20 + 中等 20 + 复杂 10），跑基线准确率
- [ ] 针对错误 case 补充 few-shot、优化 prompt，再跑一次
- [ ] README 补齐：demo 截图/GIF

- **验收**：Text2SQL 准确率 ≥ 70%（简单题应接近 100%）

### 后续：Buffer

- 修 bug、优化响应速度、录 demo 视频、写技术文章发博客/知乎

## 关键 Prompt 设计要点

### `system_persona.md` 骨架

```
你是"谢浩宇 Agent"，代表本人回答面试官和 HR 的问题。

【基本信息】
- 姓名：谢浩宇
- 目标岗位：数据分析/数据工程实习
- 技术栈：Python、SQL、Pandas、LLM API、BI 可视化

【回答风格】
- 简洁、专业、有数据支撑
- 不确定的信息说"这部分我需要查一下"
- 涉及项目细节时，用 introduce_me 工具检索知识库再回答

【工具】
- introduce_me：查我个人知识库
- query_data：查电商数据集
- visualize：画图
- explain_result：解读数据

【边界】
- 拒答涉及密码、隐私、家庭住址等敏感信息
- 不虚构没做过的项目经历
```

### Text2SQL 结构

```
你是资深数据分析师。基于以下表结构和示例，把用户问题转成 SQLite SQL。

【表结构】
{schema}

【示例】
Q: 2018 年每月订单数
A: SELECT strftime('%Y-%m', order_purchase_timestamp) AS m, COUNT(*) AS cnt
   FROM orders WHERE order_purchase_timestamp LIKE '2018%' GROUP BY m ORDER BY m;

...（5 个示例）

【要求】
- 只输出 SQL，无解释
- 只用 SELECT
- 表名列名严格匹配

【用户问题】
{question}
```

## 简历表述

**项目名**：Xiehaoyu-Agent · 基于 LLM Agent 的个人智能体与 ChatBI 系统

**链接**：GitHub 公开仓 + 公网部署地址（访问码见简历右上角）

**技术栈**：Python / LangGraph / DeepSeek / ChromaDB / SQLite / Plotly / FastAPI / Vue 3 / TypeScript / Naive UI / Nginx

**要点**：

- 设计并实现多 Tool Agent 编排架构（介绍本人 / Text2SQL 查数 / 自动可视化 / 结果解读），基于 LangGraph 状态机驱动 LLM 自主规划调用链，最多 5 轮循环推理
- Text2SQL 引擎：schema linking + few-shot prompt + sqlparse 语法校验 + 执行失败反馈自动重写，Olist 电商数据集（9 表关联）50 题自测准确率 XX%
- 构建 RAG 个人知识检索模块（BGE-large-zh 嵌入 + Chroma），支持简历/项目文档热更新，回答附带来源引用
- 前后端分离架构：FastAPI SSE 流式推送 + Vue 3 暗色主题 SPA + JWT 鉴权 + Nginx 反向代理部署
- 全链路公网部署（腾讯云轻量服务器），带访问码鉴权 + session 级 QPS 限流

## 踩坑记录

- **PowerShell stderr 误报**：Python 脚本的 stderr 输出（如 `warnings.warn()`、HF Hub 提示）在 PowerShell 中被当作 `NativeCommandError`，导致 exit code 1。实际脚本执行成功。需注意区分真错误和 stderr 警告。
- **transformers 5.x 的 torchvision 依赖**：`transformers>=5.0` 的 `zoedepth` 模块懒加载 `torchvision`，若未安装会在 Streamlit 热重载时报 `ModuleNotFoundError: No module named 'torchvision'`。不影响 Agent 正常运行，但日志会有噪声。
- **ChromaDB + sentence-transformers**：新版 ChromaDB API 有变化，`embedding_functions.SentenceTransformerEmbeddingFunction` 仍兼容但首次加载需下载 BGE 模型（约 95MB for small，约 1.3GB for large）。
- **agent trace artifact 扩展**：Day 6 需要在 UI 展示完整 DataFrame 和 Plotly figure，但原 trace 只有 summary 文本。通过在 `_run_tool` 中添加 `artifact` 字段解决，不改变 `run()` 返回签名。
- **SSE 流式推送**：LangGraph 的 `astream()` 方法每次节点执行完毕就 yield 一次 `(node_name, state_update)`，完美匹配 SSE 需求。`_serialize_artifact()` 负责将 DataFrame/Plotly Figure 转为 JSON 前端可消费。
- **Nginx proxy_buffering**：SSE 流式推送必须禁用 Nginx 缓冲 (`proxy_buffering off`)，否则前端只能在整个 agent 执行完毕后一次性收到所有事件。

## 复盘

<!-- 项目结束后补充 -->

## 时间线

- 2026-07-21：立项，方案确定
- 2026-07-22：Day 1-2 完成（数据准备 + Text2SQL）
- 2026-07-22：Day 3-4 完成（Visualize/Explain + RAG）
- 2026-07-22：Day 5 完成（LangGraph Agent 编排）
- 2026-07-23：Day 6 完成（Streamlit UI + 优化）
- 2026-07-24：Day 7-9 完成（Vue 3 + FastAPI 重构 + 部署配置）
- MVP 目标：已达成
- 迭代计划：秋招前（2026-09）持续打磨

## 相关

- [简历-数据分析方向](../../career/resume-数据分析.md)
- [简历-数据工程方向](../../career/resume-数据工程.md)
- [K12 数仓项目](../../school/基于K12线上教育场景-数仓分层＆PowerBI可视化看板/)
- [个人知识库首页](../../index.md)

## 后续迭代（MVP 之后）

按优先级排列，秋招前可选做：

1. **多数据集切换**：加个下拉菜单，支持切换到"电影评分"、"航班"等数据集，展示通用性
2. **Text2SQL 评测面板**：在 UI 里加一个 Tab，展示 50 题准确率分布 + 错题 case
3. **对话记忆持久化**：Redis / 本地文件存 session，用户下次访问延续上下文
4. **多模态输入**：支持上传 CSV，即时接入 ChatBI
5. **技术文章**：写 3 篇博客发知乎/掘金——「从 0 搭一个多 Tool Agent」「Text2SQL 工程化实践」「零成本部署 LLM 应用」，简历附链接
6. **A/B 对比**：同时接入 DeepSeek / 千问 / GLM，让用户切模型对比效果