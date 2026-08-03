# Xiehaoyu-Agent 项目概述与实施计划

## 标签

#项目 #Xiehaoyu-Agent #LLM #Agent #ChatBI #RAG #简历项目

## 项目定位

- **目标岗位**：数据方向实习/秋招（数据分析、数据工程、数据科学）
- **核心卖点**：把"自我介绍"和"数据分析能力"融进一个能跑的 Agent 产品，让面试官在见到你之前就能与你的 Agent 对话
- **完成度目标**：MVP 优先（1~2 周），后续迭代
- **成本约束**：零成本（免费云 + 免费 LLM 额度）

## 技术选型决策

| 层 | 选型 | 选型理由 |
|---|---|---|
| LLM | DeepSeek Chat API (`deepseek-v4-flash`) | 中文效果好、便宜、有免费额度；可切千问 |
| Agent 编排 | LangGraph 1.2.9+ | 状态机式，简历含金量高；支持 `astream()` 流式 |
| 后端 | FastAPI + Uvicorn | 原生 async，SSE 流式推送，按 IP 限流 |
| 前端 | Vue 3 + TypeScript + Vite + Naive UI | 暗色主题，SSE 实时接收，Plotly 图表渲染 |
| RAG 向量库 | ChromaDB（本地持久化） | 零成本，cosine 距离 |
| Embedding | BAAI/bge-large-zh-v1.5 | 通过 sentence-transformers 本地运行 |
| 数据仓库 | SQLite（本地 .db 文件） | 部署简单，够 demo |
| 可视化 | Plotly（Python 生成 JSON → 前端 plotly.js 渲染） | 交互式，零丢失 |
| 前端动画 | Lottie（lottie-web） | 6 种角色动画状态，轻量 |
| 部署 | 腾讯云轻量服务器 (2C4G) | Nginx 反向代理 + systemd 守护 |
| 鉴权/限流 | 公开访问 + 按 IP 每小时限流 + 全局每日上限 | 防刷 API |

## 架构

详见 [README.md](README.md) 架构章节。

### 状态机（LangGraph）

```
START → planner → tool_router → introduce_me/query_data/visualize/explain_result
                    ↑                    │
                    └──── 循环（≤5步）────┘
                    │
                    └──→ finalize → END
```

### 流式推送 (SSE)

```
前端 fetch POST /api/chat
  → 后端 stream_run() → app.astream()
    → 每个节点产出 yield 事件:
      - planner_decision: LLM 决策信息
      - tool_end: 工具执行结果（含序列化的 DataFrame/Plotly Figure JSON）
      - final_answer: 最终回答
    → data: [DONE] 结束
```

- `_serialize_artifact()`: DataFrame → `df_json` + `df_shape` + `df_columns`; Plotly Figure → `figure_json`
- Nginx 需配置 `proxy_buffering off` 保证 SSE 实时推送

## 实施计划（MVP，1~2 周）

### Day 1：环境 & 数据准备 ✅

- [x] 建 GitHub 仓，初始化 README、.gitignore
- [x] 建 Python venv，安装 requirements
- [x] Kaggle 下载 Olist 数据集
- [x] 写脚本把 9 个 CSV 导入 `chatbi/data/olist.db`（SQLite）
- [x] 导出 schema 描述到 `chatbi/schema.py`

**验收**：`sqlite3 olist.db "select count(*) from orders"` 能出结果 ✅ 99441 行

### Day 2：Text2SQL Tool（核心）✅

- [x] 写 `prompts/text2sql.md`：包含 schema、5 个 few-shot、输出格式约束
- [x] 写 `chatbi/validator.py`：sqlparse 校验 + 只允许 SELECT
- [x] 写 `agent/tools/query_data.py`：调 LLM → 校验 → 执行 → 失败重试（最多 3 轮）
- [x] 手写 5 个测试 case 跑通

**验收**："2018 年每月订单数" 能正确返回 DataFrame ✅ 5/5 通过

### Day 3：Visualize + Explain Tool ✅

- [x] 写 `agent/tools/visualize.py`：根据 df shape/dtype 自动选图（5 种类型）
- [x] 写 `agent/tools/explain_result.py`：LLM 解读结果

**验收**：给定 df 能画出合适图 + 输出中文解读 ✅ 4/4 通过

### Day 4：RAG（介绍我自己）Tool ✅

- [x] 写 `rag/ingest.py`：扫 8 个顶层目录下 md，按 H1/H2/H3 切片（800 字硬切 + overlap 80）
- [x] 用 BGE-large-zh-v1.5 嵌入，入 Chroma（本地缓存模型到 `rag/data/models/`）
- [x] 写 `rag/retriever.py`：top-10 检索封装
- [x] 写 `prompts/system_persona.md`：核心人设 + 边界
- [x] 写 `agent/tools/introduce_me.py`

**验收**："介绍一下你自己"、"你 K12 项目做了什么" 能给出合理回答且带引用 ✅ 4/4 通过

### Day 5：Agent 编排（LangGraph）✅

- [x] 写 `agent/planner.py`：让 LLM 输出 JSON `{action, tool, args}` 或 `{action: "finalize", answer}`
- [x] 写 `agent/llm_client.py`：共享 OpenAI 客户端工厂（消除 4 处重复代码）
- [x] 写 `agent/graph.py`：LangGraph 状态机，节点循环最多 5 步
- [x] 端到端跑通：CLI 输入问题 → 输出答案 + 轨迹

**验收**：3 类问题（纯介绍、纯查数、混合）都能走通并输出正确 tool 调用序列 ✅ 3/3 通过

### Day 6：Streamlit UI ✅

- [x] `app.py`：登录页（访问码校验）→ 主页
- [x] 主页：左边 chat，右边 3 个 Tab（Data / Chart / Trace）
- [x] 每轮对话展示 agent 轨迹（thought / tool / observation 折叠卡片）
- [x] 自定义 CSS 主题（浅色清爽风格）
- [x] session 限流：每 session 每小时 50 次
- [x] 响应式布局（桌面端双栏 + 移动端堆叠）

**验收**：本地 `streamlit run app.py` 完整体验 ✅

### Day 7~8：Vue 3 + FastAPI 重构 ✅

- [x] 后端 API 层：FastAPI + SSE 流式推送 + 按 IP 限流

- [x] `agent/graph.py` 新增 `stream_run()` 异步生成器 + `_serialize_artifact()` 序列化
- [x] `configs/settings.py` 新增 CORS/温度参数/限流配置项 + 启动安全校验
- [x] 前端核心：Vue 3 + Naive UI 暗色主题 + Pinia 状态管理 + SSE 客户端
- [x] Markdown 渲染（markdown-it + highlight.js）
- [x] 结果展示：Naive UI DataTable + SQL 折叠 + Plotly 图表渲染 + 执行轨迹时间线
- [x] 欢迎卡片：3 组快捷提问入口（自我介绍 / 数据分析 / 项目经历）
- [x] 响应式布局：桌面端侧边栏 + 移动端浮层
- [x] 代码审查通过（2026-07-24）

**验收**：前后端联调，SSE 流式推送正常，图表渲染完整 ✅

### Day 9：部署配置 + 品牌形象 ✅

- [x] Nginx 配置：SPA 静态文件 + API 反向代理 + `proxy_buffering off`
- [x] systemd 服务文件：uvicorn 守护进程
- [x] 一键部署脚本 `deploy/deploy.sh`（含 HTTPS 自动配置）
- [x] `.env.example` 更新：新增 CORS_ORIGINS、限流、Agent 参数等配置项
- [x] Lottie 动画角色系统：6 种动画状态（idle/thinking/answering/presenting/error/welcome）
- [x] 作品集主页（PortfolioView）+ 全屏聊天页（/chat）
- [x] 品牌形象整合方案设计（方案 F：2D 二次元形象动画整合）

**验收**：部署配置完整，可在服务器上一键部署 ✅

### Day 10：评测 & 打磨（进行中）

- [ ] 写 `tests/test_text2sql.py`：50 道题（简单 20 + 中等 20 + 复杂 10），跑基线准确率
- [ ] 针对错误 case 补充 few-shot、优化 prompt，再跑一次
- [ ] README 补齐：demo 截图/GIF

**验收**：Text2SQL 准确率 ≥ 70%（简单题应接近 100%）

## 后续迭代（MVP 之后）

按优先级排列，秋招前可选做：

1. **Text2SQL 评测面板**：在 UI 里加一个 Tab，展示 50 题准确率分布 + 错题 case
2. **多数据集切换**：加个下拉菜单，支持切换到"电影评分"、"航班"等数据集，展示通用性
3. **对话记忆持久化**：Redis / 本地文件存 session，用户下次访问延续上下文
4. **多模态输入**：支持上传 CSV，即时接入 ChatBI
5. **技术文章**：写 3 篇博客发知乎/掘金——「从 0 搭一个多 Tool Agent」「Text2SQL 工程化实践」「零成本部署 LLM 应用」，简历附链接
6. **A/B 对比**：同时接入 DeepSeek / 千问 / GLM，让用户切模型对比效果

## 踩坑记录

- **PowerShell stderr 误报**：Python 脚本的 stderr 输出（如 `warnings.warn()`、HF Hub 提示）在 PowerShell 中被当作 `NativeCommandError`，导致 exit code 1。实际脚本执行成功。需注意区分真错误和 stderr 警告。
- **transformers 5.x 的 torchvision 依赖**：`transformers>=5.0` 的 `zoedepth` 模块懒加载 `torchvision`，若未安装会在 Streamlit 热重载时报 `ModuleNotFoundError: No module named 'torchvision'`。不影响 Agent 正常运行，但日志会有噪声。
- **ChromaDB + sentence-transformers**：首次加载需下载 BGE 模型（约 1.3GB），已本地缓存到 `rag/data/models/`。设置 `HF_HUB_OFFLINE=1` + `TRANSFORMERS_OFFLINE=1` 避免每次启动访问 HuggingFace Hub。
- **agent trace artifact 扩展**：Day 6 需要在 UI 展示完整 DataFrame 和 Plotly figure，但原 trace 只有 summary 文本。通过在 `_run_tool` 中添加 `artifact` 字段解决，不改变 `run()` 返回签名。
- **SSE 流式推送**：LangGraph 的 `astream()` 方法每次节点执行完毕就 yield 一次 `(node_name, state_update)`，完美匹配 SSE 需求。`_serialize_artifact()` 负责将 DataFrame/Plotly Figure 转为 JSON 前端可消费。
- **Nginx proxy_buffering**：SSE 流式推送必须禁用 Nginx 缓冲（`proxy_buffering off`），否则前端只能在整个 agent 执行完毕后一次性收到所有事件。
- **DataFrame 序列化**：`_serialize_artifact()` 将 DataFrame 转为 JSON（最多 500 行），避免 `Object of type ndarray is not JSON serializable` 错误。

## 关键设计决策记录

1. **LLM 客户端提取**：4 个 tool 文件各自创建 OpenAI 客户端 → 提取为 `agent/llm_client.py` 共享工厂函数，减少重复代码
2. **限流从中间件改为依赖**：`backend/app/middleware/rate_limit.py` → `backend/app/deps/rate_limit.py`，作为普通函数在 chat router 中调用，而非 ASGI 中间件
3. **结果展示从独立面板改为内联**：ResultPanel 组件保留但未使用，结果展示改为内联到 ChatMessage.vue 中，每条消息独立展示自己的图表/数据/轨迹
4. **动画状态管理从 composable 改为 store 内置**：`useAvatarState` composable 存在但 `chat.ts` store 中直接内置了动画状态管理逻辑，更简洁
5. **Streamlit 保留兼容**：`app.py` + `ui/` 目录保留，作为快速体验入口，与 Vue 3 + FastAPI 架构并存

## 时间线

- 2026-07-21：立项，方案确定
- 2026-07-22：Day 1-5 完成（数据准备 → Agent 编排）
- 2026-07-23：Day 6 完成（Streamlit UI + 优化）
- 2026-07-24：Day 7-8 完成（Vue 3 + FastAPI 重构 + 代码审查）
- 2026-07-25：Day 9 完成（部署配置 + 品牌形象 + 项目审查）
- MVP 目标：已达成
- 迭代计划：秋招前（2026-09）持续打磨

## 相关资源

- [简历-数据分析方向](../../career/resume-数据分析.md)
- [简历-数据工程方向](../../career/resume-数据工程.md)
- [K12 数仓项目](../../school/基于K12线上教育场景-数仓分层＆PowerBI可视化看板/)
- [个人知识库首页](../../index.md)
- [Vue3-FastAPI 重构方案](docs/Vue3-FastAPI-重构方案.md)
- [代码审查记录](docs/代码审查/)
- [形象整合方案](docs/形象整合方案/)