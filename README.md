# Xiehaoyu-Agent

基于 LLM Agent 的个人智能体与 ChatBI 系统 — 谢浩宇的数字分身。

- **介绍本人**：RAG 检索个人知识库，以第一人称回答面试官/HR 关于"我是谁、做过什么"的问题
- **ChatBI**：自然语言查 Olist 巴西电商数据（Text2SQL → 自动可视化 → 结果解读）

> 公网部署地址见简历右上角 | Gitee 公开仓

## 技术栈

| 层                   | 选型                                               | 说明                                                                          |
| -------------------- | -------------------------------------------------- | ----------------------------------------------------------------------------- |
| **LLM**        | DeepSeek Chat API (`deepseek-v4-flash`)          | 中文效果好、有免费额度                                                        |
| **Agent 编排** | LangGraph 1.2.9+                                   | 状态机式，支持`astream()` 流式推送                                          |
| **后端**       | FastAPI + Uvicorn                                  | 原生 async，SSE 流式推送，按 IP 限流                                          |
| **前端**       | Vue 3 + TypeScript + Vite + Naive UI               | 深/浅色主题切换（CSS 变量驱动），SSE 实时接收，Plotly 图表渲染                |
| **RAG 向量库** | ChromaDB（本地持久化）                             | 零成本，cosine 距离                                                           |
| **Embedding**  | 智谱 embedding-3（API）/ BGE-large-zh-v1.5（本地） | 设`EMBED_API_KEY` 走 API（零本地内存），否则 sentence-transformers 本地降级 |
| **数据仓库**   | SQLite（本地 .db 文件）                            | 部署简单                                                                      |
| **数据集**     | Kaggle Olist 巴西电商                              | 9 张表关联，99441 条订单                                                      |
| **可视化**     | Plotly（Python 生成 JSON → 前端 plotly.js 渲染）  | 交互式，深/浅色主题适配                                                       |
| **动画**       | Lottie（lottie-web）                               | 6 种角色动画状态                                                              |
| **部署**       | 腾讯云轻量服务器 (2C4G)                            | Nginx 反向代理 + systemd 守护                                                 |
| **限流**       | 公开访问 + 按 IP 小时限流 + 全局每日上限           | 防刷 API                                                                      |

## 架构

```
用户浏览器 (Vue 3 + Naive UI 深/浅色主题切换)
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

目录级总览（文件级说明见各目录的 README）：

```
xiehaoyu-agent/
├── agent/          # LangGraph Agent 编排：状态机、Planner、4 个工具、输入清洗 → agent/README.md
├── backend/        # FastAPI 后端：/api/chat（SSE）、/api/sessions、限流、会话持久化 → backend/README.md
├── frontend/       # Vue 3 + TS 前端：作品集主页 + 全屏聊天页 → frontend/README.md
├── chatbi/         # Text2SQL 数据底座：schema / few-shot / SQL 校验器 → chatbi/README.md
├── rag/            # RAG 知识库：切片、Embedding 双模式、检索 → rag/README.md
├── prompts/        # LLM Prompt 模板（版本头约定）→ prompts/README.md
├── configs/        # 全局配置（.env 读取 + 启动校验）→ configs/README.md
├── deploy/         # 部署：deploy.sh / nginx.conf / systemd → deploy/README.md
├── tests/          # 三层测试：冒烟 / 单元 / 评测 → tests/README.md
├── docs/           # 过程文档归档（reviews / design / plans / references）→ docs/README.md
├── data/           # 知识库源文件与 Olist 原始数据（不入库的生产数据见 deploy/README「数据初始化」）
├── requirements.lock  # 锁定依赖版本（部署/CI 使用）
└── overview.md     # 项目概述与完整迭代时间线
```

## 核心工具（Tools）

| 工具 | 职责 | 深入文档 |
| --- | --- | --- |
| `introduce_me` | RAG 检索个人知识库（top-10 切片），LLM 生成带引用的第一人称回答 | [rag/README.md](rag/README.md) |
| `query_data` | Text2SQL：完整 schema + 10 组 few-shot → 安全校验（只允许 SELECT）→ 执行，失败反馈重试 ≤3 轮 | [chatbi/README.md](chatbi/README.md) |
| `visualize` | 纯规则自动选图（指标卡 / 折线 / 柱状 / 散点 / 表格），不调 LLM | [agent/README.md](agent/README.md) |
| `explain_result` | LLM 基于（问题 + SQL + 数据预览）输出中文业务洞察 | [agent/README.md](agent/README.md) |

编排细节（状态机、Planner 决策协议、SSE 事件、健壮性处理）：见 [agent/README.md](agent/README.md)。

### 典型数据流

| 用户问题                                          | 执行链                                                                           |
| ------------------------------------------------- | -------------------------------------------------------------------------------- |
| "介绍一下你自己"                                  | planner → introduce_me → finalize                                              |
| "2018 年每月订单数，帮我画个图"                   | planner → query_data → visualize → explain_result → finalize                 |
| "你了解电商数据吗？给我看一下 olist 的月订单趋势" | planner → introduce_me → query_data → visualize → explain_result → finalize |

## 前端功能

- **双页面**：作品集主页 `/`（左栏导航 + 关于/经历/项目/聊天入口）；全屏聊天页 `/chat`
- **聊天体验**：SSE 流式 + Markdown 渲染（代码高亮/复制）、流式光标、内联图表/数据表/SQL 折叠、执行轨迹时间线、停止生成与重试、回到底部、错误分类提示
- **主题**：深/浅色一键切换（CSS 变量驱动 + Naive UI 同步），MouseSpotlight 鼠标流光
- **动画**：6 种 Lottie 角色状态随 Agent 进度切换
- **响应式**：桌面端双栏 / 移动端堆叠

详细机制（聊天数据流、SSE 客户端、组件分层、主题体系、改文案位置）：见 [frontend/README.md](frontend/README.md)。

## API 文档

- `POST /api/chat`：SSE 流式接口，逐节点推送 `planner_decision` / `tool_end` / `final_answer` 事件，`data: [DONE]` 结束；携带 `X-User-Id` 头时启用会话记忆（注入历史 + 落库 + 后台摘要/标题）
- `/api/sessions` 系列（6 个端点，需 `X-User-Id`）：会话创建 / 列表 / 搜索 / 回放 / 重命名 / 删除；写端点独立限流（默认 120 次/时）
- `GET /api/health` / `GET /api/health/ready`：存活检查 / 就绪检查（含 DeepSeek API 探活，60s 缓存）

事件格式示例、限流规则、心跳与断连处理、会话回放协议：见 [backend/README.md](backend/README.md)。

## 快速开始

### 方式一：Vue 3 + FastAPI（推荐）

```bash
# 后端
pip install -r backend/requirements.txt   # 已包含根目录核心依赖
cp .env.example .env                      # 填入 DEEPSEEK_API_KEY
uvicorn backend.app.main:app --reload

# 前端
cd frontend
npm install
npm run dev                               # 浏览器打开 http://localhost:5173
```

### 方式二：一键部署到服务器

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

所有配置通过 `.env` 文件管理。配置加载机制（启动校验、新增配置项流程）见 [configs/README.md](configs/README.md)：

| 环境变量                 | 默认值                                   | 说明                                                         |
| ------------------------ | ---------------------------------------- | ------------------------------------------------------------ |
| `DEEPSEEK_API_KEY`     | (必填)                                   | DeepSeek API 密钥                                            |
| `DEEPSEEK_BASE_URL`    | `https://api.deepseek.com`             | API 地址                                                     |
| `DEEPSEEK_MODEL`       | `deepseek-v4-flash`                    | 模型名称                                                     |
| `IP_HOURLY_QUOTA`      | `20`                                   | 每 IP 每小时提问次数上限                                     |
| `GLOBAL_DAILY_QUOTA`   | `200`                                  | 全站每日提问总次数上限                                       |
| `SESSIONS_IP_HOURLY_QUOTA` | `120`                              | 会话写操作（创建/重命名/删除）每 IP 每小时上限               |
| `SESSIONS_DB_PATH`     | `data/sessions.db`                     | 会话存储 SQLite 文件路径                                     |
| `SESSIONS_IP_HOURLY_QUOTA` | `120`                              | 会话写端点（创建/改名/删除）每 IP 每小时上限                 |
| `CORS_ORIGINS`         | `http://localhost:5173`                | 允许的前端地址（逗号分隔）                                   |
| `MAX_AGENT_STEPS`      | `5`                                    | Agent 最大推理步数                                           |
| `SQL_RETRY_MAX`        | `3`                                    | SQL 失败最大重试次数                                         |
| `PLANNER_TEMPERATURE`  | `0.0`                                  | Planner 温度（0=确定性）                                     |
| `TEXT2SQL_TEMPERATURE` | `0.0`                                  | Text2SQL 温度                                                |
| `RAG_TEMPERATURE`      | `0.3`                                  | RAG 回答温度                                                 |
| `EXPLAIN_TEMPERATURE`  | `0.3`                                  | 数据解读温度                                                 |
| `EMBED_API_KEY`        | (空)                                     | 智谱 API Key；填入后 Embedding 切换为 API 模式（零本地内存） |
| `EMBED_API_BASE`       | `https://open.bigmodel.cn/api/paas/v4` | Embedding API 地址                                           |
| `EMBED_MODEL_NAME`     | `embedding-3`                          | Embedding 模型名称                                           |
| `EMBED_DIMENSIONS`     | `1024`                                 | 向量维度（256/512/1024/2048，切换后须重建知识库）            |
| `MEMORY_RECENT_TURNS` | `5` | 上下文携带的最近轮数 |
| `MEMORY_SUMMARY_TRIGGER_TURNS` | `10` | 触发摘要的最小总轮数 |
| `MEMORY_SUMMARY_MIN_NEW_TURNS` | `3` | 距上次摘要的最小新增轮数 |
| `MEMORY_MAX_SESSIONS_PER_USER` | `50` | 单用户会话上限 |
| `MEMORY_MAX_AGE_DAYS` | `30` | 会话过期天数 |
| `MEMORY_CLEANUP_INTERVAL_HOURS` | `6` | 清理任务间隔 |
| `SUMMARIZER_TEMPERATURE` | `0.3` | 摘要 LLM 温度 |

## 编码规范

- **模块/文件**：`snake_case`
- **类**：`PascalCase`
- **Prompt 文件**：`.md` 放 `prompts/`，代码中用 `pathlib` 读取
- **环境变量**：全大写 `SNAKE_CASE`
- **前端组件**：`PascalCase.vue`，按功能分 `portfolio/`、`chat/`
- **前端状态**：Pinia stores（`chat.ts`）
- **类型安全**：TypeScript strict mode + Pydantic schemas

## 测试

测试分层（冒烟 / 单元 / 评测）说明见 [tests/README.md](tests/README.md)。

```bash
# 冒烟测试
python -m tests.smoke_agent          # Agent 全链路（3 类问题）
python -m tests.smoke_introduce_me   # RAG 检索工具
python -m tests.smoke_text2sql       # Text2SQL 工具
python -m tests.smoke_viz_explain    # 可视化 + 解读工具

# 单元测试
pytest tests/test_rate_limit.py -v      # 限流
pytest tests/test_validator.py -v       # SQL 校验器
pytest tests/test_visualize.py -v       # 可视化选图
pytest tests/test_rag.py -v             # RAG 检索质量
pytest tests/test_text2sql.py -v        # Text2SQL pipeline（mock LLM）
pytest tests/test_planner.py -v         # Planner 决策解析
pytest tests/test_graph.py -v           # 状态机 / 工具分发
pytest tests/test_sanitize_input.py -v  # 输入清洗

# Text2SQL 基线准确率评测（50 题，需真实 DEEPSEEK_API_KEY + olist.db）
python -m tests.eval_text2sql                  # 全部 50 题
python -m tests.eval_text2sql --level easy     # 只跑简单题

# 全部测试
pytest tests/ -v
```

## 时间线

完整迭代记录见 [overview.md](overview.md)（单一事实源），此处仅列近期里程碑：

| 日期       | 里程碑                                                                                        |
| ---------- | --------------------------------------------------------------------------------------------- |
| 2026-07-25 | MVP 达成（9 天：数据准备 → Text2SQL → RAG → Agent 编排 → Vue3+FastAPI → 部署）                |
| 2026-08-05 | 提示词体系全面优化；聊天助手体验优化 12 项                                                    |
| 2026-08-06 | 对话记忆持久化：SQLite 会话存储 + 触发式摘要 + 记忆注入 + 会话侧栏                            |
| 2026-08-08 | 全项目审查（[808 报告](docs/reviews/2026-08-08-审查报告.md)）+ 当日整改：planner 解析回归、XFF 限流绕过、SQL 执行护栏、LLM 全链路异步化、中文注入模式、SSE 重试逻辑、知识库联系方式脱敏等 13 项 |
| 2026-08-08 | 评测集去泄漏：8 道与 few-shot 重叠题全部换题，无泄漏基线 96%（48/50），EASY 100% / MEDIUM 95% / HARD 90%；prompt v1.5.1 |

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
- Text2SQL 引擎：完整 schema + 10 组 few-shot prompt + sqlparse 语法校验 + 执行护栏（只读连接 / 语句超时 / 行数上限 / 禁递归 CTE）+ 失败反馈自动重写（最多 3 轮），Olist 电商数据集（9 表关联，99441 行订单）；50 题无泄漏基线准确率 96%（EASY 100% / MEDIUM 95% / HARD 90%，评测集与 few-shot 零重叠）
- 构建 RAG 个人知识检索模块（BGE-large-zh-v1.5 嵌入 + ChromaDB），支持简历/项目文档热更新，回答附带来源引用
- 前后端分离架构：FastAPI SSE 流式推送 + Vue 3 SPA（深/浅色主题）+ 按 IP 限流 + 6 种 Lottie 角色动画
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
