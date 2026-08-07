# agent/ — LangGraph Agent 编排

整个系统的"大脑"：接收用户问题，由 LLM 规划器（planner）逐步决策调用哪个工具，循环最多 5 步后输出最终回答。对外暴露同步 `run()` 和异步流式 `stream_run()` 两个入口。

## 模块

| 文件 | 职责 |
| --- | --- |
| [graph.py](graph.py) | LangGraph 状态机定义、工具节点、路由、`stream_run()` 异步生成器、`_serialize_artifact()` 序列化 |
| [planner.py](planner.py) | LLM 规划器：输出 JSON 决策 `{action, tool, args}` 或 `{action: "finalize", answer}` |
| [llm_client.py](llm_client.py) | 共享 OpenAI 客户端工厂（指向 DeepSeek，timeout 30s，max_retries 1） |
| [sanitize.py](sanitize.py) | 输入清洗：剥离代码块、检测 prompt 注入模式（planner 和 introduce_me 入口都会过一遍） |
| [tools/](tools/) | 4 个工具节点（见下） |

## 状态机

```
START → planner → (条件路由) → introduce_me / query_data / visualize / explain_result
            ↑                          │
            └────────── 循环回 planner ──┘   最多 MAX_AGENT_STEPS（默认 5）步
            │
            └→ finalize → END
```

状态 `AgentState`：`question` / `trace`（工具执行轨迹）/ `last_df` / `last_sql` / `step` / `next_action` / `next_tool` / `next_args` / `final_answer`。

- 图在模块加载时编译一次并缓存（`_app = build_graph()`），所有请求复用。
- `router()`：步数达上限、planner 决定 finalize、或返回了未知工具名时，都落入 `finalize`。
- `finalize_node()`：无显式 answer 时用最后一条 trace 兜底；若轨迹中包含 `introduce_me`，会再经一次轻量 LLM 润色（`_polish_with_persona`，temperature 0.2）保证第一人称人设。

## 工具契约

工具注册表 `TOOLS`（[graph.py](graph.py)）是路由分发的唯一事实源。

| 工具 | 输入 | 输出 | 说明 |
| --- | --- | --- | --- |
| `introduce_me` | `question` | `IntroduceResult`（answer + citations + hits） | RAG 检索个人知识库，第一人称回答，见 [rag/](../rag/README.md) |
| `query_data` | `question` | `QueryResult`（sql + df + attempts + elapsed_ms） | Text2SQL + 安全校验 + 失败反馈重试（默认最多 3 轮，指数退避），见 [chatbi/](../chatbi/README.md) |
| `visualize` | state 中的 `last_df` | `VizResult`（chart_type + figure + reason） | 纯规则自动选图（不调 LLM），5 种图表类型 |
| `explain_result` | `question` + `last_sql` + `last_df` | `str`（中文洞察文本） | 基于前 20 行数据预览生成业务洞察 |

`visualize` / `explain_result` 依赖 `query_data` 先执行（取 `last_df`），否则在 trace 中记录错误摘要，由 planner 决定下一步。

## Planner 决策协议

System prompt 在 [prompts/planner.md](../prompts/planner.md)，要求严格输出 JSON：

```json
{"action": "call", "tool": "<工具名>", "args": {"question": "..."}}
{"action": "finalize", "answer": "<最终回答>"}
```

健壮性处理（[planner.py](planner.py)）：

- `_extract_json()`：剥 markdown 代码块、转义裸控制字符、大括号配对兜底提取（应对 LLM 输出中的嵌套 `}`）。
- 空响应 fallback：LLM 返回空时按问题关键词路由（自我介绍类 → `introduce_me`，数据查询类 → `query_data`），避免误判为"无法处理"。
- 输入先经 `sanitize_input()` 清洗，防 prompt 注入。

## SSE 流式事件

`stream_run(question)` 用 LangGraph 的 `astream(stream_mode="updates")`，每个节点执行完产出一个事件：

| `type` | 触发节点 | `data` |
| --- | --- | --- |
| `planner_decision` | planner | `next_action`, `next_tool`, `step` |
| `tool_end` | 各工具 | `tool`, `args`, `summary`, `artifact`, `status`（ok/error） |
| `final_answer` | finalize | `answer`, `steps` |

`_serialize_artifact()` 把不可 JSON 序列化的对象转成前端可消费的格式：DataFrame → `df_json`（最多 500 行）+ `df_shape` + `df_columns`；Plotly Figure → `figure_json`。

## 使用

```python
from agent.graph import run, stream_run

# 同步（CLI / 测试）
result = run("2018 年每月订单数，帮我画个图", history_text="（可选）会话记忆文本")
print(result["answer"], result["steps"])

# 异步流式（FastAPI SSE，见 backend/）
async for event in stream_run("介绍一下你自己", history_text="（可选）会话记忆文本"):
    print(event["type"], event["data"])
```

## 相关配置

`MAX_AGENT_STEPS`（默认 5）、`SQL_RETRY_MAX`（默认 3）、`PLANNER_TEMPERATURE`（默认 0.0）等，见 [configs/settings.py](../configs/settings.py) 和根 README 配置参考表。

## 测试

```bash
python -m tests.smoke_agent      # 全链路冒烟（3 类问题，需真实 API Key）
pytest tests/test_graph.py -v    # 状态机 / 路由 / 工具分发（mock）
pytest tests/test_planner.py -v  # JSON 提取与决策（mock）
```
