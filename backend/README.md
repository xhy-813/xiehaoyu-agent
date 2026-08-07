# backend/ — FastAPI 后端

公开访问的 API 层：接收前端问题，驱动 [agent/](../agent/README.md) 的 LangGraph 状态机，通过 SSE 把每个执行步骤实时推给浏览器。按 IP 限流防刷。

## 结构

| 文件 | 职责 |
| --- | --- |
| [app/main.py](app/main.py) | FastAPI 入口：CORS、路由注册、结构化日志、健康检查端点 |
| [app/routers/chat.py](app/routers/chat.py) | `POST /api/chat`：SSE 流式推送 Agent 执行过程 |
| [app/deps/rate_limit.py](app/deps/rate_limit.py) | 内存限流：按 IP 每小时配额 + 全站每日上限 |
| [app/schemas/chat.py](app/schemas/chat.py) | `ChatRequest`（question，1~10000 字符） |

## API 端点

### `POST /api/chat`

请求体：

```json
{ "question": "2018 年每月订单数" }
```

响应：`text/event-stream` SSE 流，每个事件是 `{"type", "node", "data"}` 的 JSON：

```
data: {"type":"planner_decision","node":"planner","data":{"next_action":"call","next_tool":"query_data","step":1}}

data: {"type":"tool_end","node":"query_data","data":{"tool":"query_data","summary":"SQL: SELECT ...","artifact":{...},"status":"ok"}}

data: {"type":"final_answer","node":"finalize","data":{"answer":"2018 年共有 ...","steps":4}}

data: [DONE]
```

实现要点（[chat.py](app/routers/chat.py)）：

- 每 15 秒发送 `: heartbeat` 注释行保活。
- 每次迭代检查 `request.is_disconnected()`，客户端断开即停止。
- 响应头 `X-Accel-Buffering: no`，配合 Nginx `proxy_buffering off` 保证实时性（见 [deploy/nginx.conf](../deploy/nginx.conf)）。
- 异常时推送 `{"type":"error"}` 事件，不会裸断流。

### `GET /api/health` / `GET /api/health/ready`

存活检查返回 `{"status": "ok"}`；就绪检查额外验证 `DEEPSEEK_API_KEY` 已配置。

### 会话 API

所有 `/api/sessions` 端点均需携带 `X-User-Id` 请求头（UUID 格式），缺失或无效返回 400，非本人会话返回 403。

| 端点 | 方法 | 说明 |
| --- | --- | --- |
| `/api/sessions` | POST | 创建新会话 → `{"id": "<uuid>"}` |
| `/api/sessions` | GET | 列出当前用户的所有会话（按更新时间倒序） |
| `/api/sessions/search?q=` | GET | 按标题或消息内容搜索会话 |
| `/api/sessions/{id}` | GET | 获取会话详情（含消息列表） |
| `/api/sessions/{id}` | PATCH | 重命名会话（`{"title": "..."}`） |
| `/api/sessions/{id}` | DELETE | 删除会话（级联删除消息） |

实现细节见 [routers/sessions.py](app/routers/sessions.py)，会话存储与摘要机制见 [services/](../services/) 模块。

## 限流

[rate_limit.py](app/deps/rate_limit.py)，两道闸门（先查 IP，被拒请求不消耗全局名额）：

| 闸门 | 默认配额 | 配置项 | 说明 |
| --- | --- | --- | --- |
| 按 IP 每小时 | 20 次 | `IP_HOURLY_QUOTA` | 滑动窗口；空桶即时回收，避免字典无界增长 |
| 全站每日 | 200 次 | `GLOBAL_DAILY_QUOTA` | 防刷兜底，超限返回 429 |

- 真实客户端 IP 取 `X-Forwarded-For` 头（信任 Nginx 反代），生产启动需带 `--proxy-headers`（见 [deploy/xiehaoyu-agent.service](../deploy/xiehaoyu-agent.service)）。
- **限制**：内存存储，不跨进程/重启共享。多 worker 部署需换 Redis 后端（代码注释中有说明）。

## 运行

```bash
pip install -r backend/requirements.txt   # 已包含根目录核心依赖
cp .env.example .env                      # 填入 DEEPSEEK_API_KEY
uvicorn backend.app.main:app --reload     # 开发，http://127.0.0.1:8000
```

CORS 允许来源由 `CORS_ORIGINS` 配置（默认 `http://localhost:5173`）。配置项完整列表见根 README 配置参考表。

## 测试

```bash
pytest tests/test_public_chat.py -v   # 公开访问 + 健康检查
pytest tests/test_rate_limit.py -v    # 限流逻辑
```
