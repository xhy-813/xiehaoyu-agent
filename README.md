# Xiehaoyu-Agent

基于 LLM Agent 的个人智能体与 ChatBI 系统 — 谢浩宇的数字分身。

- **介绍本人**：RAG 检索个人知识库，以第一人称回答面试官/HR 关于"我是谁、做过什么"的问题
- **ChatBI**：自然语言查 Olist 巴西电商数据（Text2SQL → 自动可视化 → 结果解读）

> 公网部署地址见简历右上角 | Gitee 公开仓

## 技术栈

| 层                   | 选型                                              | 说明                                    |
| -------------------- | ------------------------------------------------- | --------------------------------------- |
| **LLM**        | DeepSeek Chat API (`deepseek-v4-flash`)         | 中文效果好、有免费额度                  |
| **Agent 编排** | LangGraph 1.2.9+                                  | 状态机式，支持`astream()` 流式推送    |
| **后端**       | FastAPI + Uvicorn                                 | 原生 async，SSE 流式推送，按 IP 限流    |
| **前端**       | Vue 3 + TypeScript + Vite + Naive UI              | 暗色主题，SSE 实时接收，Plotly 图表渲染 |
| **RAG 向量库** | ChromaDB（本地持久化）                            | 零成本，cosine 距离                     |
| **Embedding**  | BAAI/bge-large-zh-v1.5                            | 通过 sentence-transformers 本地运行     |
| **数据仓库**   | SQLite（本地 .db 文件）                           | 部署简单                                |
| **数据集**     | Kaggle Olist 巴西电商                             | 9 张表关联，99441 条订单                |
| **可视化**     | Plotly（Python 生成 JSON → 前端 plotly.js 渲染） | 交互式，暗色主题适配                    |
| **动画**       | Lottie（lottie-web）                              | 6 种角色动画状态                        |
| **部署**       | 腾讯云轻量服务器 (2C4G)                           | Nginx 反向代理 + systemd 守护           |
| **限流**       | 公开访问 + 按 IP 小时限流 + 全局每日上限           | 防刷 API                        |

## 架构

```
用户浏览器 (Vue 3 + Naive UI 暗色主题)
    │
    │ POST /api/chat (SSE 流式)
    ▼
FastAPI 后端 (公开访问，按 IP 限流)
    │
    ▼
LangGraph Agent 状态机
    │
    planner (LLM 决策) ←──────────┐
    │                             │
    ├─ introduce_me (RAG 检索) ───┤
    ├─ query_data  (Text2SQL) ────┤  循环 max 5 步
    ├─ visualize   (自动画图) ────┤
    └─ explain_result (解读) ─────┘
    │
    ▼
finalize → SSE 流式返回 (答案 + 数据 + 图表 + 轨迹)
```

### 流式推送 (SSE)

前端 fetch POST `/api/chat` → 后端 `stream_run()` → `app.astream()` 逐节点产出事件：

| 事件类型             | 触发节点 | 携带数据                                                                          |
| -------------------- | -------- | --------------------------------------------------------------------------------- |
| `planner_decision` | planner  | `next_action`, `next_tool`, `step`                                          |
| `tool_end`         | 各 tool  | `tool`, `args`, `summary`, `artifact`（含序列化的 DataFrame/Plotly JSON） |
| `final_answer`     | finalize | `answer`, `steps`                                                             |

- `_serialize_artifact()`: DataFrame → `df_json` + `df_shape` + `df_columns`; Plotly Figure → `figure_json`
- Nginx 需配置 `proxy_buffering off` 保证 SSE 实时推送

### 状态机（LangGraph）

```
START → planner → tool_router → introduce_me/query_data/visualize/explain_result
                    ↑                    │
                    └──── 循环（≤5步）────┘
                    │
                    └──→ finalize → END
```

节点：

- `planner`：调用 LLM，输入历史消息 + tool 结果，输出 JSON `{action, tool, args}` 或 `{action: "finalize", answer}`
- `tool_router`：条件边，根据 planner 输出分发到具体 tool 节点
- `introduce_me` / `query_data` / `visualize` / `explain_result`：4 个 tool 节点
- `finalize`：拼装最终回答返回用户

## 项目结构

```
xiehaoyu-agent/
├── agent/                          # LangGraph Agent 编排
│   ├── __init__.py
│   ├── graph.py                    # 状态机定义 + stream_run() + _serialize_artifact()
│   ├── planner.py                  # LLM Planner（输出 JSON 决策）
│   ├── llm_client.py               # 共享 OpenAI 客户端工厂（DeepSeek）
│   └── tools/
│       ├── __init__.py
│       ├── introduce_me.py         # RAG 个人知识库检索问答
│       ├── query_data.py           # Text2SQL + 安全校验 + 失败重试
│       ├── visualize.py            # 自动可视化（5 种图表类型）
│       └── explain_result.py       # LLM 结果解读
├── backend/                        # FastAPI 后端
│   ├── requirements.txt            # fastapi, uvicorn
│   └── app/
│       ├── __init__.py
│       ├── main.py                 # FastAPI 入口（CORS, 路由注册）
│       ├── deps/
│       │   ├── __init__.py
│       │   └── rate_limit.py       # 内存限流（按 IP 每小时 + 全局每日上限）
│       ├── routers/
│       │   ├── __init__.py
│       │   └── chat.py             # POST /api/chat（SSE 流式推送）
│       └── schemas/
│           ├── __init__.py
│           └── chat.py             # ChatRequest
├── frontend/                       # Vue 3 + TypeScript 前端
│   ├── package.json
│   ├── vite.config.ts              # Vite 配置（代理 /api → 后端）
│   ├── tsconfig.json
│   ├── index.html
│   ├── public/
│   │   └── lottie/                 # Lottie 动画 JSON 文件（6 个状态）
│   └── src/
│       ├── main.ts                 # Vue 入口（Pinia + Router）
│       ├── App.vue                 # 根组件（暗色主题 + Naive UI 配置）
│       ├── router/
│       │   └── index.ts            # /, /chat 路由
│       ├── stores/
│       │   └── chat.ts             # 聊天状态 + SSE 流式 + Lottie 动画状态管理
│       ├── api/
│       │   └── client.ts           # API 客户端（SSE chat）
│       ├── utils/
│       │   ├── sse.ts              # SSE 客户端（fetch + ReadableStream 解析）
│       │   ├── markdown.ts         # Markdown 渲染（markdown-it + highlight.js）
│       │   └── tool-constants.ts   # Tool 中文标签、颜色、图表类型映射
│       ├── composables/
│       │   └── useAvatarState.ts   # 动画状态组合式函数
│       ├── styles/
│       │   └── global.css          # 全局样式（暗色主题、滚动条、动画）
│       ├── views/
│       │   ├── PortfolioView.vue   # 作品集主页（左栏导航 + 关于/经历/项目/聊天入口）
│       │   └── ChatView.vue        # 聊天布局（响应式：顶栏 + 聊天区 + 全屏模式）
│       └── components/
│           ├── portfolio/              # 作品集组件
│           │   ├── SiteSidebar.vue     # 左栏导航（锚点滚动 + 高亮跟随）
│           │   ├── AboutSection.vue    # 关于我
│           │   ├── ExperienceSection.vue # 经历
│           │   ├── ProjectsSection.vue # 项目
│           │   ├── ChatSection.vue     # AI 问答 Banner（直达 /chat）
│           │   ├── SiteFooter.vue      # 页脚
│           │   ├── SectionHeading.vue  # 区块标题
│           │   └── MouseSpotlight.vue  # 鼠标光斑
│           └── chat/
│               ├── ChatWidget.vue      # 聊天组件（消息列表 + 输入框）
│               ├── ChatMessage.vue     # 消息气泡（Markdown 渲染 + 内联结果展示）
│               └── ChatInput.vue       # 输入框（Enter 发送，Shift+Enter 换行）
├── chatbi/                         # Text2SQL 模块
│   ├── __init__.py
│   ├── schema.py                   # 9 张 Olist 表完整 schema 描述
│   ├── few_shots.py                # 5 组 (问题, SQL) few-shot 示例
│   ├── validator.py                # SQL 安全校验（sqlparse + 黑名单）
│   ├── load_olist.py               # CSV → SQLite 导入脚本
│   └── data/                       # SQLite 数据库文件（olist.db）
├── rag/                            # RAG 知识库模块
│   ├── __init__.py                 # 懒加载导出
│   ├── constants.py                # 共享常量（COLLECTION, EMBED_MODEL）
│   ├── ingest.py                   # 语料切片 + 向量入库（BGE-large-zh-v1.5）
│   ├── retriever.py                # Chroma top-k 检索封装（支持缓存失效）
│   └── data/
│       └── chroma/                 # Chroma 持久化向量库
├── prompts/                        # LLM Prompt 模板
│   ├── system_persona.md           # Agent 核心人设（第一人称 + 回答风格 + 知识库说明 + 边界）
│   ├── planner.md                  # Planner 决策 prompt（工具选择 + 规则 + 边界情况）
│   ├── introduce_me.md             # RAG 回答 prompt（检索片段 + 格式约束）
│   ├── text2sql.md                 # Text2SQL 模板（schema + few-shot + 质量规范 + 反面示例）
│   └── explain.md                  # 数据解读模板（洞察要求 + 业务背景 + 正反面示例）
├── configs/
│   ├── __init__.py
│   └── settings.py                 # 全局配置（API key, JWT, 限流, 温度参数, 启动校验）
├── deploy/                         # 部署配置
│   ├── deploy.sh                   # 一键部署脚本（Ubuntu 20.04+）
│   ├── nginx.conf                  # Nginx 配置（SPA + API 代理 + SSE 禁用缓冲）
│   └── xiehaoyu-agent.service     # systemd 服务文件
├── tests/                          # 测试
│   ├── __init__.py
│   ├── smoke_agent.py              # Agent 全链路冒烟测试（3 类问题）
│   ├── smoke_introduce_me.py       # RAG 工具测试
│   ├── smoke_text2sql.py           # Text2SQL 工具测试
│   ├── smoke_viz_explain.py        # 可视化 + 解读工具测试
│   ├── test_rate_limit.py          # 限流单元测试
│   ├── test_text2sql.py            # Text2SQL 准确率评测（50 题，待完成）
│   ├── test_rag.py                 # RAG 检索质量测试
│   ├── test_validator.py           # SQL 校验器测试
│   └── test_visualize.py           # 可视化选图逻辑测试
├── docs/                           # 设计文档
│   ├── Vue3-FastAPI-重构方案.md    # 重构方案设计文档
│   ├── 代码审查/                    # 代码审查记录
│   └── 形象整合方案/                # 角色形象 Lottie 动画整合方案
├── data/                           # 数据文件
│   ├── olist数据集/                 # Kaggle Olist CSV 源文件
│   └── 知识库/                      # 个人知识库（简历/自我介绍/常见问题/项目/工作经历）
├── app.py                          # Streamlit 入口（原版 UI，保留兼容）
├── requirements.txt                # Python 核心依赖
├── README.md                       # 本文件
├── overview.md                     # 项目概述与实施计划
├── .env.example                    # 环境变量模板
├── .gitignore                      # Git 忽略规则
└── LICENSE                         # 开源许可证
```

## 功能详解

### Tool 1: `introduce_me` — 个人知识库检索

**流程**：用户问题 → BGE-large-zh-v1.5 嵌入 → Chroma 向量检索 top-10 → 构造 RAG prompt → LLM 生成第一人称回答

**输入**：`question`（关于本人的问题）

**输出**：`IntroduceResult`（回答文本 + 引用来源列表，含文件路径、标题、相似度分数）

**语料来源**：个人知识库中 `简历/`、`自我介绍/`、`常见问题/`、`项目/`、`工作经历/` 下所有 `.md` 文件

**切片策略**：按 Markdown H1/H2/H3 标题切分；单段超过 800 字则硬切，重叠 80 字

**人设 Prompt** (`prompts/system_persona.md`)：

- 身份：谢浩宇的数字分身，吉首大学 2023 级数据科学与大数据技术专业
- 风格：第一人称、具体有细节、有数字支撑、结构清晰、自然真诚
- 边界：不泄露密码/隐私/家庭住址、不虚构项目经历

### Tool 2: `query_data` — Text2SQL 查数据

**流程**：用户问题 → 完整 schema + 5 个 few-shot 示例 → LLM 生成 SQL → sqlparse 语法校验 → 执行 → 失败反馈重试（最多 3 轮）

**输入**：`question`（自然语言数据问题）

**输出**：`QueryResult`（SQL 字符串 + 结果 DataFrame + 执行耗时 + 重试次数 + 执行轨迹）

**安全校验** (`chatbi/validator.py`)：

- 只允许单条语句
- 只允许 `SELECT` / `WITH ... SELECT`
- 关键字黑名单：`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `REPLACE`, `ATTACH`, `DETACH`, `PRAGMA`, `VACUUM`, `REINDEX`, `GRANT`, `REVOKE`

**Few-shot 示例**（5 组）：

1. 时间过滤 + 聚合："2018 年每月的订单数"
2. 分组统计："支付方式的分布（订单数）"
3. JOIN + 排序："销量 top 5 的商品品类（用英文品类名）"
4. 多表 JOIN："各州（customer_state）的下单客户数 top 10"
5. 条件聚合："已送达订单的平均评分"

**Olist 数据集**（9 张表）：
`customers` · `orders` · `order_items` · `order_payments` · `order_reviews` · `products` · `sellers` · `category_translation` · `geolocation`

### Tool 3: `visualize` — 自动可视化

**自动选图规则**（按优先级）：

1. 1 行 1 列数值 → 指标卡（Indicator）
2. 时间序列（1 时间列 + 1~N 数值列）→ 折线图
3. 分类 + 数值（分类数 ≤ 30）→ 柱状图（按数值降序）
4. 两个数值列 → 散点图
5. 兜底 → 表格

**时间列识别**：`dtype=datetime` 或列名含 `date/time/month/year/day/timestamp/ts/dt/created_at/updated_at`

**输出**：`VizResult`（Plotly Figure + chart_type + reason）

### Tool 4: `explain_result` — 结果解读

**流程**：LLM 基于 (question, SQL, 数据预览) 输出 1~2 条中文业务洞察

**输出**：解读文本

### 典型数据流

| 用户问题                                          | 执行链                                                                           |
| ------------------------------------------------- | -------------------------------------------------------------------------------- |
| "介绍一下你自己"                                  | planner → introduce_me → finalize                                              |
| "2018 年每月订单数，帮我画个图"                   | planner → query_data → visualize → explain_result → finalize                 |
| "你了解电商数据吗？给我看一下 olist 的月订单趋势" | planner → introduce_me → query_data → visualize → explain_result → finalize |

## 前端功能

### 页面结构

- **作品集页** (`/`)：暗色主题个人作品集（左栏导航 + 关于/经历/项目/聊天入口）
- **聊天页** (`/chat`)：顶栏 + 聊天区 + 公开访问

### 聊天功能

- **Markdown 渲染**：支持代码高亮（highlight.js）、表格、引用、链接
- **流式光标**：流式输出中显示闪烁光标 `▊`
- **内联结果展示**：每条 assistant 消息下方直接展示图表 + 数据表 + 执行轨迹
- **SQL 折叠**：SQL 语句默认折叠，点击展开
- **执行轨迹时间线**：带颜色编码的步骤时间线（蓝=查询 / 绿=图表 / 橙=检索 / 紫=解读）
- **一键复制**：hover 消息气泡显示复制按钮
- **快捷提问**：欢迎卡片提供 3 组快捷入口（自我介绍 / 数据分析 / 项目经历）

### 响应式布局

- 桌面端（>980px）：左栏固定 + 右栏内容
- 移动端（≤980px）：顶部身份块 + 横向导航 + 纵向内容

### 主题

- 暗色主题（CSS 变量驱动）
- 主色调：`#63e2b7`（青绿色）

## API 文档

### `POST /api/chat`

请求体：

```json
{ "question": "2018 年每月订单数" }
```

响应：`text/event-stream` SSE 流

```
data: {"type":"planner_decision","node":"planner","data":{"next_action":"call","next_tool":"query_data","step":1}}

data: {"type":"tool_end","node":"query_data","data":{"tool":"query_data","summary":"SQL: SELECT ...","artifact":{"sql":"SELECT ...","df_json":"[...]","df_shape":{"rows":12,"cols":2},"df_columns":["month","cnt"]}}}

data: {"type":"final_answer","node":"finalize","data":{"answer":"2018 年共有 12 个月的数据...","steps":4}}

data: [DONE]
```

### `GET /api/health`

响应：

```json
{ "status": "ok" }
```

## 快速开始

### 方式一：Streamlit 快速体验

```bash
# 1. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate            # Linux/Mac
# .venv\Scripts\activate             # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env                 # 填入 DEEPSEEK_API_KEY

# 4. 启动
streamlit run app.py
```

### 方式二：Vue 3 + FastAPI 生产模式

```bash
# 后端
pip install -r requirements.txt
pip install -r backend/requirements.txt
cp .env.example .env                 # 填入 DEEPSEEK_API_KEY
uvicorn backend.app.main:app --reload

# 前端
cd frontend
npm install
npm run dev                          # 浏览器打开 http://localhost:5173
```

### 方式三：一键部署到服务器

```bash
# 适用于 Ubuntu 20.04+ / 腾讯云轻量服务器
chmod +x deploy/deploy.sh
sudo ./deploy.sh                     # 或 sudo ./deploy.sh your-domain.com（自动配置 HTTPS）
```

部署脚本执行步骤：

1. 安装系统依赖（Python, Nginx, certbot）
2. 克隆/更新代码
3. 安装 Python 依赖（含 FastAPI）
4. 配置环境变量（`.env`）
5. 构建前端（`npm install && npm run build`）
6. 配置 Nginx + systemd
7. 可选：获取 SSL 证书

## 配置参考

所有配置通过 `.env` 文件管理：

| 环境变量                 | 默认值                       | 说明                                               |
| ------------------------ | ---------------------------- | -------------------------------------------------- |
| `DEEPSEEK_API_KEY`     | (必填)                       | DeepSeek API 密钥                                  |
| `DEEPSEEK_BASE_URL`    | `https://api.deepseek.com` | API 地址                                           |
| `DEEPSEEK_MODEL`       | `deepseek-v4-flash`        | 模型名称                                           |
| `IP_HOURLY_QUOTA`     | `20`                      | 每 IP 每小时提问次数上限                           |
| `GLOBAL_DAILY_QUOTA`  | `200`                     | 全站每日提问总次数上限                             |
| `CORS_ORIGINS`         | `http://localhost:5173`    | 允许的前端地址（逗号分隔）                         |
| `MAX_AGENT_STEPS`      | `5`                        | Agent 最大推理步数                                 |
| `SQL_RETRY_MAX`        | `3`                        | SQL 失败最大重试次数                               |
| `PLANNER_TEMPERATURE`  | `0.0`                      | Planner 温度（0=确定性）                           |
| `TEXT2SQL_TEMPERATURE` | `0.0`                      | Text2SQL 温度                                      |
| `RAG_TEMPERATURE`      | `0.3`                      | RAG 回答温度                                       |
| `EXPLAIN_TEMPERATURE`  | `0.3`                      | 数据解读温度                                       |

## 编码规范

- **模块/文件**：`snake_case`
- **类**：`PascalCase`
- **Prompt 文件**：`.md` 放 `prompts/`，代码中用 `pathlib` 读取
- **环境变量**：全大写 `SNAKE_CASE`
- **前端组件**：`PascalCase.vue`，按功能分 `portfolio/`、`chat/`
- **前端状态**：Pinia stores（`chat.ts`）
- **类型安全**：TypeScript strict mode + Pydantic schemas

## 测试

```bash
# 冒烟测试
python -m tests.smoke_agent          # Agent 全链路（3 类问题）
python -m tests.smoke_introduce_me   # RAG 检索工具
python -m tests.smoke_text2sql       # Text2SQL 工具
python -m tests.smoke_viz_explain    # 可视化 + 解读工具

# 单元测试
pytest tests/test_rate_limit.py -v   # 限流
pytest tests/test_validator.py -v    # SQL 校验器
pytest tests/test_visualize.py -v    # 可视化选图
pytest tests/test_rag.py -v          # RAG 检索质量

# 全部测试
pytest tests/ -v
```

## 时间线

| 日期       | 里程碑                                    |
| ---------- | ----------------------------------------- |
| 2026-07-21 | 立项，方案确定                            |
| 2026-07-22 | Day 1-2: 数据准备 + Text2SQL              |
| 2026-07-22 | Day 3-4: Visualize/Explain + RAG          |
| 2026-07-22 | Day 5: LangGraph Agent 编排               |
| 2026-07-23 | Day 6: Streamlit UI + 优化                |
| 2026-07-24 | Day 7-8: Vue 3 + FastAPI 重构 + 代码审查  |
| 2026-07-25 | Day 9: 部署配置 + 形象整合方案 + 项目审查 |
| 2026-07-25 | MVP 达成 ✓                               |
| 2026-07-27 | 知识库改造 v1: 重构为求职导向的 5 分类 21 文件 + 向量库重建 |
| 2026-07-28 | Prompt 优化: 提取 planner/introduce_me 到文件 + text2sql/explain 增强 + RAG 代码重构 |

## 后续迭代

1. **Text2SQL 评测面板**：50 题准确率基线 + 错题分析
2. **多数据集切换**：支持电影评分、航班等数据集
3. **对话记忆持久化**：Redis / 本地文件存 session
4. **多模态输入**：支持上传 CSV 即时接入 ChatBI
5. **A/B 对比**：同时接入 DeepSeek / 千问 / GLM
6. **技术文章**：博客发知乎/掘金

## 简历表述

**项目名**：Xiehaoyu-Agent · 基于 LLM Agent 的个人智能体与 ChatBI 系统

**技术栈**：Python / LangGraph / DeepSeek / ChromaDB / SQLite / Plotly / FastAPI / Vue 3 / TypeScript / Naive UI / Nginx

**要点**：

- 设计并实现多 Tool Agent 编排架构（介绍本人 / Text2SQL 查数 / 自动可视化 / 结果解读），基于 LangGraph 状态机驱动 LLM 自主规划调用链，最多 5 轮循环推理
- Text2SQL 引擎：完整 schema + few-shot prompt + sqlparse 语法校验 + 执行失败反馈自动重写（最多 3 轮），Olist 电商数据集（9 表关联，99441 行订单）
- 构建 RAG 个人知识检索模块（BGE-large-zh-v1.5 嵌入 + ChromaDB），支持简历/项目文档热更新，回答附带来源引用
- 前后端分离架构：FastAPI SSE 流式推送 + Vue 3 暗色主题 SPA + 按 IP 限流 + 6 种 Lottie 角色动画
- 全链路公网部署（腾讯云轻量服务器），公开访问 + 按 IP 限流 + 全局日上限

## 踩坑记录

- **PowerShell stderr 误报**：Python 脚本的 stderr 输出（如 `warnings.warn()`）在 PowerShell 中被当作 `NativeCommandError`，导致 exit code 1
- **transformers 5.x 的 torchvision 依赖**：`transformers>=5.0` 的 `zoedepth` 模块懒加载 `torchvision`，若未安装会在 Streamlit 热重载时报错，不影响 Agent 正常运行
- **ChromaDB + sentence-transformers**：首次加载需下载 BGE 模型（约 1.3GB），已缓存到 HF 缓存目录（`~/.cache/huggingface/hub/`），设置 `HF_HUB_OFFLINE=1` 可离线运行
- **SSE 流式推送**：LangGraph 的 `astream()` 方法每次节点执行完毕就 yield 一次，完美匹配 SSE 需求
- **Nginx proxy_buffering**：SSE 流式推送必须禁用 Nginx 缓冲（`proxy_buffering off`），否则前端只能一次性收到所有事件
- **DataFrame 序列化**：`_serialize_artifact()` 将 DataFrame 转为 JSON（最多 500 行），Plotly Figure 转为 JSON，避免 `Object of type ndarray is not JSON serializable` 错误

## License

MIT
