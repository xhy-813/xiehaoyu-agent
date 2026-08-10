# Xiehaoyu-Agent: Streamlit → Vue 3 + FastAPI 重构方案

> **状态**: ✅ 已完成（2026-07-24）
>
> 所有 4 个 Phase 已实施完毕，项目已成功从 Streamlit 迁移到 Vue 3 + FastAPI 架构。

## Context

当前项目使用 Streamlit 做 Web UI，存在三个核心痛点：布局不够灵活、交互体验不够流畅（每次操作刷新）、视觉风格很难做出 ChatGPT/Claude 那种 AI 产品的质感。用户希望用 Vue 3 + FastAPI 重构，部署到腾讯云轻量服务器，实现更稳定、更低延迟、更专业的体验。

## 架构决策总览

| 决策 | 选择 | 理由 |
|---|---|---|
| 前端框架 | Vue 3 + Vite + TypeScript | 用户明确要求 |
| UI 组件库 | Naive UI | 暗色主题内置，设计语言接近 ChatGPT，中文生态好 |
| 后端框架 | FastAPI | 用户明确要求，原生 async 支持 SSE |
| 流式推送 | SSE (Server-Sent Events) | 单向推送足够，比 WebSocket 轻量 |
| 项目结构 | Monorepo (frontend/ + backend/) | 统一管理，agent/chatbi/rag 保持不动 |
| 鉴权 | 访问码 → JWT Token | 保留现有 access code 模式，升级为 JWT |
| 图表渲染 | 后端 Plotly → JSON → 前端 plotly.js 渲染 | 零丢失，标准做法 |
| 部署 | 腾讯云轻量服务器 (2C4G) | 国内低延迟，稳定，¥50-68/月 |
| 目标用户 | 个位数用户，低并发 | 无需考虑扩展性 |

## 关键技术突破

### LangGraph `astream()` 实现 SSE 流式推送

当前 `agent/graph.py` 使用同步 `app.invoke()`，一次性返回结果。LangGraph 1.2.9 原生支持 `astream()` 方法，每次节点执行完毕就 yield 一次 `(node_name, state_update)`。这完美匹配 SSE 需求——每一步工具执行后就能拿到新 trace，无需修改任何现有节点代码。

只需在 `agent/graph.py` 中新增 `stream_run()` 函数，将 `astream()` 的输出转换为 SSE 事件格式。

### Plotly + DataFrame 序列化

- Plotly Figure: `fig.to_json()` → 前端 `Plotly.newPlot()` 渲染
- DataFrame: `df.head(500).to_json(orient="records")` → 前端 Naive UI DataTable
- 限制序列化大小，避免超大 payload

## 实施阶段

### Phase 1: 后端 API 层 ✅ 已完成

**目标**: FastAPI 后端独立运行，SSE 流式推送可用

#### 目录结构
```
backend/
├── requirements.txt          # fastapi, uvicorn, PyJWT
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口 (CORS, 路由注册)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py          # POST /api/auth/login (access_code → JWT)
│   │   └── chat.py          # POST /api/chat (SSE 流式响应)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py          # LoginRequest, TokenResponse
│   │   └── chat.py          # ChatRequest
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── rate_limit.py    # 内存限流 (每小时配额)
│   └── dependencies.py      # JWT 验证 FastAPI Depends
```

#### 修改的现有文件

1. **[configs/settings.py](../../configs/settings.py)** — 新增 3 个配置项:
   - `jwt_secret: str` (JWT 签名密钥)
   - `jwt_expire_hours: int = 24`
   - `cors_origins: str` (前端地址，开发环境 localhost:5173)

2. **[agent/graph.py](../../agent/graph.py)** — 新增:
   - `stream_run()` 异步生成器：使用 `app.astream()` 流式执行 agent，每步 yield 一个事件
   - `_serialize_artifact()` 函数: DataFrame → `df_json` + `df_shape` + `df_columns`, Plotly Figure → `figure_json`

#### 关键 API 设计

**POST /api/auth/login**
```json
// Request:  {"access_code": "xxx"}
// Response: {"access_token": "eyJ...", "token_type": "bearer"}
```

**POST /api/chat** (SSE 流)
```json
// Request:  {"question": "2018年每月订单数"}
// Headers:  Authorization: Bearer eyJ...
// Response: text/event-stream
//   data: {"type":"planner_decision","node":"planner","data":{...}}
//   data: {"type":"tool_end","node":"query_data","data":{"tool":"query_data","summary":"...","artifact":{"sql":"...","df_json":"[...]","df_shape":{...}}}}
//   data: {"type":"tool_end","node":"visualize","data":{"tool":"visualize","artifact":{"figure_json":"{...}","chart_type":"line"}}}
//   data: {"type":"final_answer","node":"finalize","data":{"answer":"...","steps":3}}
//   data: [DONE]
```

**限流**: 从 `ui/auth.py` 迁移到 `backend/app/middleware/rate_limit.py`，使用内存字典存储时间戳。

#### 验证方式
```bash
# 启动后端
uvicorn backend.app.main:app --reload
# 测试登录
curl -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d '{"access_code":"test"}'
# 测试 SSE 流
curl -X POST http://localhost:8000/api/chat -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"question":"介绍一下你自己"}' --no-buffer
```

### Phase 2: Vue 3 前端核心 ✅ 已完成

**目标**: 登录、发送消息、接收流式回答

#### 技术栈
- Vue 3.5+ (Composition API + `<script setup>`)
- Vite 8
- Naive UI (darkTheme)
- Pinia (状态管理)
- Vue Router 4
- markdown-it + highlight.js
- plotly.js-dist
- 原生 fetch (ReadableStream 实现 SSE 接收)

#### 组件树
```
App.vue
└── <n-config-provider :theme="darkTheme">
    └── <router-view />

LoginView.vue          — 访问码输入 + 登录
ChatView.vue           — 主布局
├── ChatSidebar.vue    — 配额信息、清空对话、技术栈
├── ChatMain.vue       — 对话列表 + 输入框
│   ├── WelcomeCard.vue     — 快捷问题 (空对话时)
│   ├── ChatMessage.vue (×N) — 消息气泡 + Markdown 渲染 + 内联结果
│   └── ChatInput.vue       — 输入框
```

> **实际实现调整**: 结果面板未使用独立右侧面板，而是嵌入到 `ChatMessage.vue` 中作为内联结果展示（数据表 + 图表 + 可折叠轨迹），更适合移动端响应式布局。

#### 路由
- `/login` — 登录页 (未登录默认)
- `/chat` — 聊天页 (需登录)
- 其他路径 → 重定向到 `/chat`

#### 核心状态管理 (Pinia)

**auth store**: `isAuthenticated`, `token`, `login()`, `logout()`
**chat store**: `messages`, `currentTrace`, `isStreaming`, `sendMessage()`, `clearChat()`

`sendMessage()` 流程:
1. 添加用户消息到 `messages`
2. 创建占位助手消息
3. 调用 `fetch('/api/chat', {method: 'POST', body: {question}})` 获取 ReadableStream
4. 逐行解析 SSE: `tool_end` → 追加到 `currentTrace`, `final_answer` → 更新助手消息内容
5. `[DONE]` → 完成

#### SSE 客户端实现
不使用 `EventSource`（不支持 POST + 自定义 Header），改用 `fetch` + `ReadableStream`:
```typescript
const response = await fetch('/api/chat', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({ question }),
})
const reader = response.body!.getReader()
// 逐行读取 data: {...} 事件
```

#### 验证方式
```bash
cd frontend && npm install && npm run dev
# 浏览器打开 localhost:5173
# 输入访问码 → 进入聊天页 → 发送消息 → 观察流式响应
```

### Phase 3: 结果面板 + 打磨 ✅ 已完成

- **ResultData** (`ChatMessage.vue` 内联): Naive UI `<n-data-table>` 渲染 DataFrame，`<n-code>` 展示 SQL（可折叠）
- **ResultChart** (`ChartRenderer.vue`): 接收 `figure_json`，用 `Plotly.newPlot()` 渲染，响应式
- **ResultTrace** (`ChatMessage.vue` 内联): 可折叠时间线步骤卡片，展示工具名、参数、摘要
- **ResultSummary**: 由 `ChatMessage.vue` 底部的步骤标签替代（步数 + 工具类型标签）
- 流式更新: 每收到 `tool_end` 事件实时追加到 `currentTrace`
- 响应式布局: 移动端侧边栏改为浮层覆盖
- 错误处理: spinner 加载态 / 错误提示

> **实际实现差异**: 原计划独立右侧 `ResultPanel.vue` 组件，实际改为内联到 `ChatMessage.vue` 中，每条助手消息内部直接展示该次查询的数据表、图表和轨迹。这种方式更符合 ChatGPT-style 对话体验，且自动适应移动端。

### Phase 4: 部署上线 ✅ 已完成

**部署架构**:
```
腾讯云轻量服务器 (2C4G, 5Mbps, Ubuntu 22.04)
├── Nginx :80/:443
│   ├── /api/* → proxy_pass http://127.0.0.1:8000 (proxy_buffering off)
│   └── /* → /srv/xiehaoyu-agent/frontend/dist/ (try_files $uri /index.html)
├── FastAPI (uvicorn, 127.0.0.1:8000, systemd 守护)
└── Let's Encrypt HTTPS 证书 (certbot)
```

**关键 Nginx 配置**:
- `proxy_buffering off` — SSE 流式推送必须禁用缓冲
- `proxy_read_timeout 300s` — agent 执行可能耗时较长
- `try_files $uri /index.html` — SPA 路由

**部署步骤**:
1. 服务器克隆仓库到 `/srv/xiehaoyu-agent`
2. 创建 venv，安装依赖
3. 配置 `.env` (DEEPSEEK_API_KEY, ACCESS_CODE, JWT_SECRET)
4. `cd frontend && npm install && npm run build`
5. 配置 Nginx (静态文件 + API 代理)
6. 配置 systemd 服务 (uvicorn 守护进程)
7. certbot 获取 HTTPS 证书
8. 冒烟测试

**部署文件**:
- [deploy/deploy.sh](../../deploy/deploy.sh) — 一键部署脚本
- [deploy/nginx.conf](../../deploy/nginx.conf) — Nginx 配置
- [deploy/xiehaoyu-agent.service](../../deploy/xiehaoyu-agent.service) — systemd 服务文件

## 可复用现有代码

| 现有代码 | 复用方式 |
|---|---|
| `agent/graph.py` 的 `build_graph()`, `_run_tool()`, `_summarize()` | 保持不动，新增 `stream_run()` 调用 `astream()` |
| `agent/planner.py` 的 `plan()` | 完全不变，`stream_run()` 复用相同的 planner_node |
| 所有 `agent/tools/*.py` | 完全不变，工具节点逻辑零修改 |
| `chatbi/` 全部模块 | 完全不变 |
| `rag/` 全部模块 | 完全不变 |
| `prompts/` 全部模板 | 完全不变 |
| `configs/settings.py` | 新增 3 个字段 (jwt_secret, jwt_expire_hours, cors_origins)，其余不变 |
| `ui/auth.py` 限流逻辑 | 迁移到 `backend/app/middleware/rate_limit.py` |
| 测试文件 | 全部保留，`tests/` 目录不变 |

## 可删除的旧代码

- `app.py` — Streamlit 入口，被 FastAPI 替代（保留作为快速体验入口）
- `ui/` — 整个目录，被 Vue 前端替代（保留作为 Streamlit 备选方案）

> **实际决策**: 保留 Streamlit 代码不动，作为快速本地体验的备选方案。两种 UI 共存，共享同一套 agent/chatbi/rag 核心代码。

## 实际实现与计划的差异

1. **结果面板布局**: 原计划独立右侧 `ResultPanel`，实际改为内联到 `ChatMessage.vue` 中，更符合 ChatGPT 风格
2. **ResultSummary**: 原计划独立指标卡片组件，实际简化为消息底部的步骤标签
3. **Embedding 模型**: `rag/ingest.py` 中从 `BAAI/bge-small-zh-v1.5` 升级为 `BAAI/bge-large-zh-v1.5`（更好的检索效果）
4. **知识库目录**: 从 5 个扩展到 8 个（新增 `life/`, `methods/`, `templates/`）
5. **前端版本**: 实际使用 Vite 8 + Vue 3.5+，较计划中版本更新

## 验证方式

### Phase 1 验证
```bash
# 启动后端
uvicorn backend.app.main:app --reload
# curl 测试 SSE 流式响应
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $(curl -s -X POST http://localhost:8000/api/auth/login \
    -H 'Content-Type: application/json' \
    -d '{"access_code":"test"}' | python -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')" \
  -H "Content-Type: application/json" \
  -d '{"question":"2018年每月订单数，帮我画个图"}' --no-buffer
```

### Phase 2-3 验证
```bash
# 启动前端开发服务器
cd frontend && npm run dev
# 浏览器 localhost:5173 → 登录 → 发送消息 → 验证流式响应 + 图表渲染
```

### Phase 4 验证
```bash
# 构建前端
cd frontend && npm run build
# 用 Nginx 代理 + 生产 uvicorn 启动
# 浏览器访问 https://your-domain.com → 全流程验证
```

### 现有测试保留
```bash
python -m tests.smoke_agent        # 全链路冒烟测试
python -m tests.smoke_introduce_me  # RAG 工具测试
python -m tests.smoke_text2sql      # Text2SQL 测试
python -m tests.smoke_viz_explain   # 可视化+解读测试
```