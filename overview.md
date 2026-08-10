# Xiehaoyu-Agent 项目概述与实施计划

## 标签

#项目 #Xiehaoyu-Agent #LLM #Agent #ChatBI #RAG #简历项目

## 项目定位

- **目标岗位**：数据方向实习/秋招（数据分析、数据工程、数据科学）
- **核心卖点**：把"自我介绍"和"数据分析能力"融进一个能跑的 Agent 产品，让面试官在见到你之前就能与你的 Agent 对话
- **完成度目标**：MVP 优先（1~2 周），后续迭代
- **成本约束**：零成本（免费云 + 免费 LLM 额度）

## 技术选型决策

| 层         | 选型                                              | 选型理由                                                       |
| ---------- | ------------------------------------------------- | -------------------------------------------------------------- |
| LLM        | DeepSeek Chat API (`deepseek-v4-flash`)         | 中文效果好、便宜、有免费额度；可切千问                         |
| Agent 编排 | LangGraph 1.2.9+                                  | 状态机式，简历含金量高；支持`astream()` 流式                 |
| 后端       | FastAPI + Uvicorn                                 | 原生 async，SSE 流式推送，按 IP 限流                           |
| 前端       | Vue 3 + TypeScript + Vite + Naive UI              | 深/浅色主题切换（CSS 变量驱动），SSE 实时接收，Plotly 图表渲染 |
| RAG 向量库 | ChromaDB（本地持久化）                            | 零成本，cosine 距离                                            |
| Embedding  | 智谱 embedding-3（API）/ BGE-large-zh-v1.5（本地） | 设 `EMBED_API_KEY` 走 API（零本地内存），否则本地降级         |
| 数据仓库   | SQLite（本地 .db 文件）                           | 部署简单，够 demo                                              |
| 可视化     | Plotly（Python 生成 JSON → 前端 plotly.js 渲染） | 交互式，零丢失                                                 |
| 前端动画   | Lottie（lottie-web）                              | 6 种角色动画状态，轻量                                         |
| 部署       | 腾讯云轻量服务器 (2C4G)                           | Nginx 反向代理 + systemd 守护                                  |
| 鉴权/限流  | 公开访问 + 按 IP 每小时限流 + 全局每日上限        | 防刷 API                                                       |

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

- [X] 建 GitHub 仓，初始化 README、.gitignore
- [X] 建 Python venv，安装 requirements
- [X] Kaggle 下载 Olist 数据集
- [X] 写脚本把 9 个 CSV 导入 `chatbi/data/olist.db`（SQLite）
- [X] 导出 schema 描述到 `chatbi/schema.py`

**验收**：`sqlite3 olist.db "select count(*) from orders"` 能出结果 ✅ 99441 行

### Day 2：Text2SQL Tool（核心）✅

- [X] 写 `prompts/text2sql.md`：包含 schema、5 个 few-shot、输出格式约束
- [X] 写 `chatbi/validator.py`：sqlparse 校验 + 只允许 SELECT
- [X] 写 `agent/tools/query_data.py`：调 LLM → 校验 → 执行 → 失败重试（最多 3 轮）
- [X] 手写 5 个测试 case 跑通

**验收**："2018 年每月订单数" 能正确返回 DataFrame ✅ 5/5 通过

### Day 3：Visualize + Explain Tool ✅

- [X] 写 `agent/tools/visualize.py`：根据 df shape/dtype 自动选图（5 种类型）
- [X] 写 `agent/tools/explain_result.py`：LLM 解读结果

**验收**：给定 df 能画出合适图 + 输出中文解读 ✅ 4/4 通过

### Day 4：RAG（介绍我自己）Tool ✅

- [X] 写 `rag/ingest.py`：扫 8 个顶层目录下 md，按 H1/H2/H3 切片（800 字硬切 + overlap 80）
- [X] 用 BGE-large-zh-v1.5 嵌入，入 Chroma（模型缓存到 HF 缓存目录；后改造为智谱 API 优先、本地 BGE 兜底）
- [X] 写 `rag/retriever.py`：top-10 检索封装
- [X] 写 `prompts/system_persona.md`：核心人设 + 边界
- [X] 写 `agent/tools/introduce_me.py`

**验收**："介绍一下你自己"、"你 K12 项目做了什么" 能给出合理回答且带引用 ✅ 4/4 通过

### Day 5：Agent 编排（LangGraph）✅

- [X] 写 `agent/planner.py`：让 LLM 输出 JSON `{action, tool, args}` 或 `{action: "finalize", answer}`
- [X] 写 `agent/llm_client.py`：共享 OpenAI 客户端工厂（消除 4 处重复代码）
- [X] 写 `agent/graph.py`：LangGraph 状态机，节点循环最多 5 步
- [X] 端到端跑通：CLI 输入问题 → 输出答案 + 轨迹

**验收**：3 类问题（纯介绍、纯查数、混合）都能走通并输出正确 tool 调用序列 ✅ 3/3 通过

### Day 6：Streamlit UI ✅

- [X] `app.py`：登录页（访问码校验）→ 主页
- [X] 主页：左边 chat，右边 3 个 Tab（Data / Chart / Trace）
- [X] 每轮对话展示 agent 轨迹（thought / tool / observation 折叠卡片）
- [X] 自定义 CSS 主题（浅色清爽风格）
- [X] session 限流：每 session 每小时 50 次
- [X] 响应式布局（桌面端双栏 + 移动端堆叠）

**验收**：本地 `streamlit run app.py` 完整体验 ✅

> 注：Streamlit UI 已在架构迁移至 Vue 3 + FastAPI 后移除（`app.py` + `ui/`），正式入口为 Vue 3 + FastAPI。

### Day 7~8：Vue 3 + FastAPI 重构 ✅

- [X] 后端 API 层：FastAPI + SSE 流式推送 + 按 IP 限流
- [X] `agent/graph.py` 新增 `stream_run()` 异步生成器 + `_serialize_artifact()` 序列化
- [X] `configs/settings.py` 新增 CORS/温度参数/限流配置项 + 启动安全校验
- [X] 前端核心：Vue 3 + Naive UI 暗色主题 + Pinia 状态管理 + SSE 客户端
- [X] Markdown 渲染（markdown-it + highlight.js）
- [X] 结果展示：Naive UI DataTable + SQL 折叠 + Plotly 图表渲染 + 执行轨迹时间线
- [X] 欢迎卡片：3 组快捷提问入口（自我介绍 / 数据分析 / 项目经历）
- [X] 响应式布局：桌面端侧边栏 + 移动端浮层
- [X] 代码审查通过（2026-07-24）

**验收**：前后端联调，SSE 流式推送正常，图表渲染完整 ✅

### Day 9：部署配置 + 品牌形象 ✅

- [X] 部署配置（`deploy.sh` 一键部署 + Nginx 反代 + systemd 守护）
- [X] 前端作品集主页（PortfolioView）+ 全屏聊天页（/chat）
- [X] 品牌形象整合方案设计（方案 F：2D 二次元形象动画整合）

**验收**：部署配置完整，可在服务器上一键部署 ✅

### Day 10：评测 & 打磨 ✅

- [X] 写 `tests/eval_text2sql.py`：50 道题（简单 20 + 中等 20 + 复杂 10），执行准确率判定
- [X] 跑基线准确率，针对错误 case 补充 few-shot、优化 prompt，再跑一次（共 8 轮迭代）
- [ ] README 补齐：demo 截图/GIF

**验收**：Text2SQL 准确率 96%（48/50），EASY 100% / MEDIUM 95% / HARD 90% ✅（目标 ≥70%；2026-08-08 去泄漏换题后的无重叠基线）

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
- **ChromaDB + sentence-transformers**：首次加载需下载 BGE 模型（约 1.3GB），缓存到 HF 缓存目录（`~/.cache/huggingface/hub/`）。设置 `HF_HUB_OFFLINE=1` + `TRANSFORMERS_OFFLINE=1` 避免每次启动访问 HuggingFace Hub。2026-08-04 起支持智谱 embedding-3 API 模式（设 `EMBED_API_KEY` 即切换，零本地内存）。
- **agent trace artifact 扩展**：Day 6 需要在 UI 展示完整 DataFrame 和 Plotly figure，但原 trace 只有 summary 文本。通过在 `_run_tool` 中添加 `artifact` 字段解决，不改变 `run()` 返回签名。
- **SSE 流式推送**：LangGraph 的 `astream()` 方法每次节点执行完毕就 yield 一次 `(node_name, state_update)`，完美匹配 SSE 需求。`_serialize_artifact()` 负责将 DataFrame/Plotly Figure 转为 JSON 前端可消费。
- **Nginx proxy_buffering**：SSE 流式推送必须禁用 Nginx 缓冲（`proxy_buffering off`），否则前端只能在整个 agent 执行完毕后一次性收到所有事件。
- **DataFrame 序列化**：`_serialize_artifact()` 将 DataFrame 转为 JSON（最多 500 行），避免 `Object of type ndarray is not JSON serializable` 错误。

## 关键设计决策记录

1. **LLM 客户端提取**：4 个 tool 文件各自创建 OpenAI 客户端 → 提取为 `agent/llm_client.py` 共享工厂函数，减少重复代码
2. **限流从中间件改为依赖**：`backend/app/middleware/rate_limit.py` → `backend/app/deps/rate_limit.py`，作为普通函数在 chat router 中调用，而非 ASGI 中间件
3. **结果展示从独立面板改为内联**：ResultPanel 组件保留但未使用，结果展示改为内联到 ChatMessage.vue 中，每条消息独立展示自己的图表/数据/轨迹
4. **动画状态管理内置 store**：不单独抽 `useAvatarState` composable，`chat.ts` store 直接内置动画状态管理逻辑，更简洁
5. **Streamlit 已移除**：`app.py` + `ui/` 目录已在架构迁移完成后清理，正式入口为 Vue 3 + FastAPI
6. **Embedding 双模式**：本地 BGE 在 2C4G 服务器上内存吃紧 → `rag/constants.py` 提供工厂函数，设 `EMBED_API_KEY` 即切换智谱 embedding-3 API（零本地内存），未设则降级本地 BGE（见 [API_Embedding改造方案](docs/design/2026-08-04-API-Embedding改造方案.md)）
7. **评测脚本独立命名**：50 题基线评测放 `tests/eval_text2sql.py`（需真实 API Key，执行准确率判定），`test_text2sql.py` 保留为 mock LLM 的 pipeline 单元测试

## 时间线

- 2026-07-21：立项，方案确定
- 2026-07-22：Day 1-5 完成（数据准备 → Agent 编排）
- 2026-07-23：Day 6 完成（Streamlit UI + 优化）
- 2026-07-24：Day 7-8 完成（Vue 3 + FastAPI 重构 + 代码审查）
- 2026-07-25：Day 9 完成（部署配置 + 品牌形象 + 项目审查）
- MVP 目标：已达成
- 2026-07-27：知识库改造 v1：重构为求职导向的 5 分类 21 文件 + 向量库重建
- 2026-07-28：Prompt 优化：提取 planner/introduce_me 到文件 + text2sql/explain 增强 + RAG 代码重构
- 2026-07-29：前端深浅色主题系统（CSS 变量体系 + useTheme + Naive UI 动态切换）
- 2026-07-29：MouseSpotlight 重写（background-attachment:fixed，滚动时光斑正确跟随）
- 2026-07-29：前端组件主题适配，消除全部硬编码颜色，SectionHeading 移动端响应式
- 2026-08-02：全屏聊天页 /chat 重写 + 聊天组件全链路深色适配
- 2026-08-03：清理重构遗留（去 JWT、Streamlit 旧应用公开化、限流空桶回收）
- 2026-08-04：Embedding 改造为智谱 AI API（本地 BGE 兜底降级）+ 安全审查整改 + requirements.lock 锁定依赖
- 2026-08-05：聊天助手体验优化 12 项（WelcomeScreen、代码块复制、回到底部、停止生成重试、错误分类、移动端适配）
- 2026-08-05：提示词体系全面优化 + ChatMessage 拆分（MessageBubble + InlineResult）+ planner 空响应处理
- 2026-08-06：移除 Streamlit UI 残留（app.py + ui/）+ planner 健壮性修复（空响应 fallback 路由、裸控制字符转义）
- 2026-08-06：Text2SQL 评测 8 轮迭代：50 题基线 96%（EASY 100% / MEDIUM 100% / HARD 80%）；prompt v1.5、few-shot 扩至 10 组；评测器改为值指纹对齐、忽略列名
- 2026-08-08：808 全项目审查整改（planner 解析回归、限流 XFF 绕过、SQL 执行护栏、中文注入模式、SSE 重试、知识库脱敏）；评测集去泄漏换题 8 道，无泄漏基线 96%（EASY 100% / MEDIUM 95% / HARD 90%）
- 2026-08-09：docs/ 归档重组（reviews / design / plans / references 四类 + 统一日期命名）+ 各模块 README 漂移修复（backend/chatbi/agent/rag/frontend/tests）+ 根 README 项目结构改为目录级 + 时间线以本文件为单一事实源
- 2026-08-10：面试官视角体验优化 T1-T4 实施（[08-09 方案](docs/design/2026-08-09-面试官视角体验优化方案.md)）：秋招文案口径统一 + 新增 00-求职意向权威事实源；联系方式放开（ingest PII 豁免白名单 + 13-联系方式.md）；流式期间切会话 confirm 中断；citations 引用来源折叠区、429 限流文案透传、Olist 公开数据集标注、快捷问题重设计为完整演示链、错误气泡 CSS 变量化、聊天页转化出口（联系我弹层 + /resume.pdf 下载）、移动端侧栏 overlay 抽屉、prefers-color-scheme 跟随系统、流式 60s 中间态提示；persona v1.3.0 / explain v1.2.1；向量库重建（153 chunks）；303 单测全绿
- 迭代计划：秋招前（2026-09）持续打磨

## 相关资源

- [简历-数据分析方向](../../career/resume-数据分析.md)
- [简历-数据工程方向](../../career/resume-数据工程.md)
- [K12 数仓项目](../../school/基于K12线上教育场景-数仓分层＆PowerBI可视化看板/)
- [个人知识库首页](../../index.md)
- [Vue3-FastAPI 重构方案](docs/design/2026-07-24-Vue3-FastAPI-重构方案.md)
- [审查报告归档](docs/reviews/)
- [形象整合方案](docs/design/2026-07-25-形象整合方案/)
