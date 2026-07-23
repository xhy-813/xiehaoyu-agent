# Day 6: Streamlit UI 设计文档

## 概述

为 Xiehaoyu-Agent 实现 Streamlit Web UI，包含访问码鉴权、聊天交互、执行轨迹展示和数据可视化。基于 `overview.md` Day 6 规划。

## 目标

- 本地 `streamlit run app.py` 完整体验
- 面试官可通过公网链接 + 访问码与 Agent 对话
- 每轮对话展示 agent 执行轨迹（thought / tool / observation）
- session 级限流防刷 API

## 架构决策

### 扩展 agent trace 携带原始结果对象

**问题**：当前 `agent/graph.py` 的 `run()` 返回的 trace 只包含 summary 文本（如 SQL + 前10行预览），但 UI 的 Data Tab 需要完整 DataFrame，Chart Tab 需要 Plotly figure。

**方案**：扩展 trace 条目结构，让每个 tool 调用携带原始结果对象。

```python
# 当前 trace 条目
{"tool": "query_data", "args": {...}, "summary": "SQL: ..."}

# 扩展后
{"tool": "query_data", "args": {...}, "summary": "SQL: ...",
 "artifact": {"sql": "...", "df": <DataFrame>}}

{"tool": "visualize", "args": {...}, "summary": "图表类型: line",
 "artifact": {"figure": <Figure>, "chart_type": "line"}}

{"tool": "introduce_me", "args": {...}, "summary": "...",
 "artifact": {"answer": "...", "citations": [...]}}

{"tool": "explain_result", "args": {...}, "summary": "...",
 "artifact": {"insight": "..."}}
```

在 `agent/graph.py` 的 `_run_tool` 中把已有的 tool 返回值（QueryResult / VizResult / str）挂到 `artifact` 字段。不改变 `run()` 的返回签名，只是 trace 条目变"重"了。

## UI 布局

```
未登录 → 访问码输入页
已登录 → 主页（layout="wide"）
  ┌─────────────────────┬──────────────────────────┐
  │  左侧 (60%)          │  右侧 (40%)               │
  │  Chat 对话区          │  Tabs: [Data | Chart | Trace] │
  │  - st.chat_message   │  - Data: 最新查询的 DataFrame │
  │  - st.chat_input      │  - Chart: 最新 Plotly 图表   │
  │  - 历史消息            │  - Trace: 执行轨迹折叠卡片    │
  └─────────────────────┴──────────────────────────┘
```

## 组件设计

### `ui/auth.py` — 访问码校验 + 限流

- `check_access() -> bool`：检查 `session_state["authenticated"]`，未登录时渲染访问码输入框，校验 `settings.access_code`
- `check_rate_limit() -> bool`：session_state 存 `query_timestamps: list[float]`，每次提问前检查过去 1 小时内的次数，超过 `settings.session_hourly_quota`（20）则拒绝并提示用户

### `ui/chat.py` — 聊天组件

- `render_chat()`：渲染聊天历史（从 `session_state["messages"]`）+ 输入框
- 用户输入后调用 `agent.graph.run(question)`，将结果存入 `session_state["last_result"]`
- 用 `st.chat_message` 渲染用户和 assistant 消息
- assistant 消息下方显示步数和工具调用摘要

### `ui/trace.py` — 执行轨迹 + 数据/图表展示

- `render_data(trace)`：从 trace 中找最后一个带 `artifact.df` 的条目，用 `st.dataframe` 展示完整 DataFrame
- `render_chart(trace)`：从 trace 中找最后一个带 `artifact.figure` 的条目，用 `st.plotly_chart` 展示
- `render_trace(trace)`：遍历 trace，每个条目用 `st.expander` 渲染折叠卡片，标题为 `tool(args)`，内容为 summary

### `app.py` — 入口

```python
def main():
    st.set_page_config(page_title="Xiehaoyu-Agent", layout="wide")
    if not check_access():
        return  # 渲染访问码页
    # 已登录 → 主页
    col_chat, col_side = st.columns([3, 2])
    with col_chat:
        render_chat()
    with col_side:
        tab_data, tab_chart, tab_trace = st.tabs(["Data", "Chart", "Trace"])
        result = st.session_state.get("last_result")
        if result:
            with tab_data: render_data(result["trace"])
            with tab_chart: render_chart(result["trace"])
            with tab_trace: render_trace(result["trace"])
```

## 数据流

```
用户输入 → chat.py 调 run(question)
  → agent 执行（planner → tools → finalize）
  → 返回 {answer, trace[+artifacts], steps}
  → chat.py 存 session_state["messages"] 和 session_state["last_result"]
  → 右侧 Tabs 从 last_result["trace"] 提取 artifact 渲染
```

## 限流设计

- 粒度：每 session 每小时
- 阈值：`settings.session_hourly_quota`（默认 20）
- 实现：`session_state["query_timestamps"]` 存时间戳列表，每次提问前清理 1 小时前的记录，检查剩余数量
- 超限时：不调用 agent，直接返回提示"本小时提问次数已达上限（20 次），请稍后再试"

## 错误处理

- Agent 执行异常：在 chat 区域显示错误信息，不影响后续对话
- API 超时/限流：显示友好提示，建议重试
- 空结果：Data/Chart Tab 显示"暂无数据"提示

## 验收标准

- `streamlit run app.py` 本地启动无报错
- 输入访问码后进入主页
- 三类问题（纯介绍 / 纯查数 / 混合）都能正常对话
- 纯查数类问题：Data Tab 显示 DataFrame，Chart Tab 显示图表，Trace Tab 显示执行轨迹
- 连续提问 20 次后触发限流提示
