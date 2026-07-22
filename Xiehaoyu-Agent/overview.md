# Xiehaoyu-Agent 项目概述

## 标签

#项目 #Xiehaoyu-Agent #LLM #Agent #ChatBI #RAG #简历项目

## 项目概述

Xiehaoyu-Agent 是一个代表本人的对外 LLM Agent，兼具两大能力：

1. **介绍本人**：基于 RAG 检索个人知识库（简历、项目、实习经历），回答面试官/HR 关于"我是谁、做过什么"的问题。
2. **ChatBI（自然语言查数据）**：面向公开电商数据集，支持 Text2SQL、SQL 自动纠错重试、结果自动可视化、多轮追问、结果自然语言解读。

面试官可通过公网链接 + 访问码直接体验，作为简历上的差异化亮点项目。

## 项目定位

- **目标岗位**：数据方向实习/秋招（数据分析、数据工程、数据科学）
- **核心卖点**：把"自我介绍"和"数据分析能力"融进一个能跑的 Agent 产品，让面试官在见到你之前就能与你的 Agent 对话
- **完成度目标**：MVP 优先（1~2 周），后续迭代
- **成本约束**：零成本（免费云 + 免费 LLM 额度）

## 技术栈

| 层         | 选型                                                   | 备注                                                 |
| ---------- | ------------------------------------------------------ | ---------------------------------------------------- |
| LLM        | DeepSeek Chat API                                      | 中文效果好、便宜、有免费额度；可切千问               |
| Agent 编排 | LangGraph                                              | 状态机式，简历含金量高；备选 LangChain AgentExecutor |
| RAG 向量库 | ChromaDB（本地持久化）                                 | 零成本                                               |
| Embedding  | BAAI/bge-small-zh-v1.5                                 | 通过 sentence-transformers 本地跑                    |
| 数据仓库   | SQLite（本地 .db 文件）                                | 部署简单，够 demo                                    |
| 数据集     | Kaggle Olist 巴西电商                                  | 9 张表关联，字段清晰                                 |
| 可视化     | Plotly                                                 | 交互式、Streamlit 原生支持                           |
| Web UI     | Streamlit                                              | 快速搭建、部署方便                                   |
| 部署       | HuggingFace Spaces（Streamlit runtime）                | 免费公网，送 HTTPS 域名                              |
| 鉴权/限流  | Streamlit session_state + 访问码 + 单 session QPS 限制 | 防刷 API                                             |
| 代码托管   | GitHub（公开仓）                                       | 简历附链接                                           |

## 架构

### 总览

```
用户浏览器
    │
    ▼
Streamlit Web UI（HF Spaces）
    │  聊天框 | 数据表 | 图表 | 执行轨迹侧栏
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
└────────────────────────────────────────┘
    │           │            │
    ▼           ▼            ▼
Chroma      SQLite       Plotly
个人知识库    电商数据      图表 JSON
```

### 状态机（LangGraph）

节点：

- `planner`：调用 LLM，输入历史消息 + tool 结果，输出下一步动作（调用哪个 tool，或结束）
- `tool_router`：根据 planner 输出分发到具体 tool 节点
- `introduce_me` / `query_data` / `visualize` / `explain_result`：4 个 tool 节点
- `finalize`：拼装最终回答返回用户

边：

- planner → tool_router → 各 tool → planner（循环，最多 5 轮防死循环）
- planner → finalize（当 LLM 判断已足够回答）

### Tool 详细设计

#### Tool 1: `introduce_me(question: str)`

- 输入：关于本人的问题
- 流程：
  1. 用 BGE 嵌入 question
  2. Chroma 向量检索 top-5 相关文档片段
  3. 构造 RAG prompt：`system(人设) + retrieved_chunks + question`
  4. LLM 生成回答
- 输出：回答文本 + 引用来源（文件路径）
- 语料来源：`career/`、`school/`、`work/`、`projects/`、`tech/` 下所有 md
- 切片策略：按 markdown H2/H3 切，或固定 500 字 + overlap 50

#### Tool 2: `query_data(question: str, history_sql: list = None)`

- 输入：自然语言数据问题（+ 历史 SQL，用于多轮追问）
- 流程（Text2SQL 工程化）：
  1. **Schema Linking**：把 question 与所有表名/列名做嵌入相似度，取 top-3 表的 schema
  2. **Few-shot Prompt**：内置 5 个高质量 (question, SQL) 示例
  3. LLM 生成 SQL
  4. **SQL 校验**：sqlparse 语法检查 + 只允许 SELECT（防注入）
  5. 执行 SQL
  6. **失败重试**：若报错，把错误信息 + 原 SQL 反馈给 LLM 重写，最多 3 轮
- 输出：SQL 字符串 + 结果 DataFrame + 执行耗时

#### Tool 3: `visualize(df: DataFrame, question: str)`

- 输入：查询结果 + 用户问题
- 自动选图规则：
  - 1 行 1 列数值 → 大数字指标卡
  - 分类 + 数值（≤20 类）→ 柱状图
  - 时间序列 → 折线图
  - 两个数值列 → 散点图
  - 兜底 → 表格
- 输出：Plotly figure JSON

#### Tool 4: `explain_result(df, sql, question)`

- LLM 用自然语言解读结果，给出 1~2 条业务洞察
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
me-agent/                    # 仓库目录名保留小写 kebab-case
├── app.py                    # Streamlit 入口 + 鉴权 + 限流
├── agent/
│   ├── __init__.py
│   ├── graph.py              # LangGraph 定义
│   ├── planner.py            # LLM Planner prompt
│   └── tools/
│       ├── introduce_me.py
│       ├── query_data.py
│       ├── visualize.py
│       └── explain_result.py
├── rag/
│   ├── ingest.py             # 语料切片 + 入库脚本
│   ├── retriever.py          # 检索封装
│   └── data/chroma/          # 本地向量库
├── chatbi/
│   ├── schema.py             # 表结构描述
│   ├── few_shots.py          # Text2SQL 示例
│   ├── validator.py          # SQL 校验
│   └── data/olist.db         # SQLite 数据
├── ui/
│   ├── chat.py               # 聊天组件
│   ├── trace.py              # 执行轨迹侧栏
│   └── auth.py               # 访问码校验
├── prompts/
│   ├── system_persona.md     # 核心人设
│   ├── text2sql.md
│   └── explain.md
├── configs/
│   └── settings.py           # API key、模型名、限流参数
├── tests/
│   ├── test_text2sql.py      # Text2SQL 准确率评测（50 题）
│   └── test_rag.py
├── requirements.txt
├── README.md                 # 项目介绍 + 架构图 + 部署说明
└── .env.example              # DEEPSEEK_API_KEY, ACCESS_CODE
```

### 命名约定

- 模块/文件：`snake_case`
- 类：`PascalCase`
- Prompt 文件：`.md` 放 `prompts/`，代码里用 `pathlib` 读
- 环境变量：全大写 `SNAKE_CASE`

### 依赖清单（requirements.txt）

```
streamlit>=1.32
langgraph>=0.0.40
langchain-core>=0.1.40
openai>=1.20            # 用来调 DeepSeek（兼容 OpenAI SDK）
chromadb>=0.4.24
sentence-transformers>=2.5
sqlparse>=0.4
sqlalchemy>=2.0
pandas>=2.1
plotly>=5.20
python-dotenv>=1.0
```

## 实施计划（MVP，1~2 周）

按天分解，每天可交付、可验证。

### Day 1：环境 & 数据准备

- [ ] 建 GitHub 仓 `me-agent`，初始化 README、.gitignore（`.env`、`data/`、`__pycache__`）
- [ ] 建 Python venv，安装 requirements
- [ ] Kaggle 下载 [Olist 数据集](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- [ ] 写脚本把 9 个 CSV 导入 `chatbi/data/olist.db`（SQLite）
- [ ] 在 SQLite 里补充表关系注释，导出 schema 描述到 `chatbi/schema.py`

- **验收**：`sqlite3 olist.db "select count(*) from orders"` 能出结果

### Day 2：Text2SQL Tool（核心）

- [ ] 写 `prompts/text2sql.md`：包含 schema、5 个 few-shot、输出格式约束
- [ ] 写 `chatbi/validator.py`：sqlparse 校验 + 只允许 SELECT
- [ ] 写 `agent/tools/query_data.py`：调 LLM → 校验 → 执行 → 失败重试（最多 3 轮）
- [ ] 手写 5 个测试 case 跑通

- **验收**："2018 年每月订单数" 能正确返回 DataFrame

### Day 3：Visualize + Explain Tool

- [ ] 写 `agent/tools/visualize.py`：根据 df shape/dtype 自动选图
- [ ] 写 `agent/tools/explain_result.py`：LLM 解读结果

- **验收**：给定 df 能画出合适图 + 输出中文解读

### Day 4：RAG（介绍我自己）Tool

- [ ] 写 `rag/ingest.py`：扫 `career/`、`school/`、`work/`、`projects/`、`tech/` 下 md，按 H2 切片
- [ ] 用 BGE-small-zh 嵌入，入 Chroma
- [ ] 写 `rag/retriever.py`：top-5 检索封装
- [ ] 写 `prompts/system_persona.md`：核心人设 + 边界（拒答 `secrets/`）
- [ ] 写 `agent/tools/introduce_me.py`

- **验收**："介绍一下你自己"、"你 K12 项目做了什么" 能给出合理回答且带引用

### Day 5：Agent 编排（LangGraph）

- [ ] 写 `agent/planner.py`：让 LLM 输出 JSON `{action, tool, args}` 或 `{action: "finalize", answer}`
- [ ] 写 `agent/graph.py`：LangGraph 状态机，节点循环最多 5 步
- [ ] 端到端跑通：CLI 输入问题 → 输出答案 + 轨迹

- **验收**：3 类问题（纯介绍、纯查数、混合）都能走通并输出正确 tool 调用序列

### Day 6：Streamlit UI

- [ ] `app.py`：登录页（访问码校验）→ 主页
- [ ] 主页：左边 chat，右边 3 个 Tab（Data / Chart / Trace）
- [ ] 每轮对话展示 agent 轨迹（thought / tool / observation 折叠卡片）
- [ ] session 限流：每 session 每小时 20 次

- **验收**：本地 `streamlit run app.py` 完整体验

### Day 7：评测 & 打磨

- [ ] 写 `tests/test_text2sql.py`：50 道题（简单 20 + 中等 20 + 复杂 10），跑基线准确率
- [ ] 针对错误 case 补充 few-shot、优化 prompt，再跑一次
- [ ] README 补齐：项目介绍、架构图、部署说明、demo 截图/GIF

- **验收**：Text2SQL 准确率 ≥ 70%（简单题应接近 100%）

### Day 8：部署

- [ ] 在 HuggingFace 建 Space（Streamlit template）
- [ ] 添加 Secret：`DEEPSEEK_API_KEY`、`ACCESS_CODE`
- [ ] push 代码，验证公网访问
- [ ] 生成访问二维码，加到简历 & 个人网站

- **验收**：手机打开链接 → 输入访问码 → 完整对话流程可用

### Day 9~10：Buffer

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

**链接**：`https://huggingface.co/spaces/xhy/me-agent`（访问码见简历右上角）

**技术栈**：Python / LangGraph / DeepSeek / ChromaDB / SQLite / Streamlit / Plotly / HuggingFace Spaces

**要点**：

- 设计并实现多 Tool Agent 编排架构（介绍本人 / Text2SQL 查数 / 自动可视化 / 结果解读），基于 LangGraph 状态机驱动 LLM 自主规划调用链，最多 5 轮循环推理
- Text2SQL 引擎：schema linking + few-shot prompt + sqlparse 语法校验 + 执行失败反馈自动重写，Olist 电商数据集（9 表关联）50 题自测准确率 XX%
- 构建 RAG 个人知识检索模块（BGE-zh 嵌入 + Chroma），支持简历/项目文档热更新，回答附带来源引用
- 全链路公网部署（HuggingFace Spaces），带访问码鉴权 + session 级 QPS 限流，零成本运行

## 踩坑记录

<!-- 开发中补充 -->

## 复盘

<!-- 项目结束后补充 -->

## 时间线

- 2026-07-21：立项，方案确定
- MVP 目标：2026-08-04 前完成部署上线
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
