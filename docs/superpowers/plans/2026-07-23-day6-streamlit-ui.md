# Day 6 Streamlit UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 Streamlit Web UI，包含访问码鉴权、聊天交互、执行轨迹展示和数据可视化。

**Architecture:** 扩展 agent/graph.py 的 trace 携带原始结果对象（df/figure/sql），UI 层从 trace 提取 artifact 展示 Data/Chart/Trace 三个 Tab。左侧聊天区 60%，右侧 Tab 区 40%。

**Tech Stack:** Streamlit, Plotly, pandas, LangGraph

## Global Constraints

- Python 3.11, 依赖已安装（requirements.txt）
- 访问码从 `configs/settings.py` 的 `settings.access_code` 读取
- 限流阈值 `settings.session_hourly_quota`（默认 20）
- Agent 最大步数 `settings.max_agent_steps`（默认 5）
- 不改变 `agent.graph.run()` 的返回签名 `{"answer", "trace", "steps"}`
- Streamlit session_state 管理会话状态

---

### Task 1: 扩展 agent trace 携带 artifact

**Files:**
- Modify: `agent/graph.py:46-92`（`_summarize` 和 `_run_tool` 函数）

**Interfaces:**
- Produces: trace 条目新增 `artifact` 字段，结构如下：
  - `introduce_me`: `{"answer": str, "citations": list[dict]}`
  - `query_data`: `{"sql": str, "df": pd.DataFrame}`
  - `visualize`: `{"figure": go.Figure, "chart_type": str}`
  - `explain_result`: `{"insight": str}`

- [ ] **Step 1: 修改 `_run_tool` 函数，在每个 tool 分支添加 artifact**

在 `agent/graph.py` 的 `_run_tool` 函数中，修改各 tool 的返回值，添加 artifact 字段：

```python
def _run_tool(tool: str, args: dict, state: AgentState) -> dict:
    """Execute one tool, return state patch."""
    question = args.get("question", state["question"])
    trace = state.get("trace", [])

    if tool == "introduce_me":
        r = introduce_me(question)
        artifact = {"answer": r.answer, "citations": r.citations}
        return {"trace": trace + [{"tool": tool, "args": args, "summary": _summarize(tool, r), "artifact": artifact}]}

    if tool == "query_data":
        r = query_data(question)
        artifact = {"sql": r.sql, "df": r.df}
        return {
            "trace": trace + [{"tool": tool, "args": args, "summary": _summarize(tool, r), "artifact": artifact}],
            "last_df": r.df,
            "last_sql": r.sql,
        }

    if tool == "visualize":
        df = state.get("last_df")
        if df is None:
            return {"trace": trace + [{"tool": tool, "args": args, "summary": "错误: 没有数据，请先调用 query_data", "artifact": None}]}
        r = visualize(df, question)
        artifact = {"figure": r.figure, "chart_type": r.chart_type}
        return {"trace": trace + [{"tool": tool, "args": args, "summary": _summarize(tool, r), "artifact": artifact}]}

    if tool == "explain_result":
        df = state.get("last_df")
        sql = state.get("last_sql", "")
        if df is None:
            return {"trace": trace + [{"tool": tool, "args": args, "summary": "错误: 没有数据，请先调用 query_data", "artifact": None}]}
        r = explain_result(question, sql, df)
        artifact = {"insight": r}
        return {"trace": trace + [{"tool": tool, "args": args, "summary": _summarize(tool, r), "artifact": artifact}]}

    raise ValueError(f"Unknown tool: {tool}")
```

- [ ] **Step 2: 运行冒烟测试验证 trace 扩展不破坏现有功能**

Run: `python -m tests.smoke_agent`
Expected: 3 个 case 全部通过，输出 "All cases passed."

- [ ] **Step 3: 验证 artifact 字段存在**

Run:
```powershell
@'
from agent.graph import run
result = run("2018年每月订单数")
for t in result["trace"]:
    print(t["tool"], "has artifact:", "artifact" in t)
    if "artifact" in t and t["artifact"]:
        if "df" in t["artifact"]:
            print("  df shape:", t["artifact"]["df"].shape)
        if "figure" in t["artifact"]:
            print("  chart_type:", t["artifact"]["chart_type"])
'@ | python -
```
Expected: query_data 的 artifact 有 df，visualize 的 artifact 有 figure

- [ ] **Step 4: Commit**

```bash
git add agent/graph.py
git commit -m "feat(agent): trace 携带 artifact（df/figure/sql）"
```

---

### Task 2: 实现 ui/auth.py（访问码校验 + 限流）

**Files:**
- Create: `ui/auth.py`

**Interfaces:**
- Consumes: `configs.settings.settings.access_code`, `configs.settings.settings.session_hourly_quota`
- Produces:
  - `check_access() -> bool`：检查登录状态，未登录时渲染访问码输入框
  - `check_rate_limit() -> bool`：检查 session 限流，超限返回 False

- [ ] **Step 1: 实现 ui/auth.py**

```python
"""Access-code gate + session hourly rate limit."""

from __future__ import annotations

import time

import streamlit as st

from configs.settings import settings


def check_access() -> bool:
    """Return True if user is authenticated. Renders login form if not."""
    if st.session_state.get("authenticated"):
        return True

    st.markdown("## Xiehaoyu-Agent")
    st.markdown("请输入访问码以继续")

    code = st.text_input("访问码", type="password", placeholder="请输入访问码")
    if st.button("进入", type="primary"):
        if code == settings.access_code:
            st.session_state["authenticated"] = True
            st.session_state["query_timestamps"] = []
            st.rerun()
        else:
            st.error("访问码错误，请重试")

    st.markdown("---")
    st.caption("如需访问码，请联系：谢浩宇")
    return False


def check_rate_limit() -> bool:
    """Return True if under hourly quota. Updates timestamp list on success."""
    now = time.time()
    timestamps = st.session_state.get("query_timestamps", [])
    # 清理 1 小时前的记录
    cutoff = now - 3600
    timestamps = [t for t in timestamps if t > cutoff]

    if len(timestamps) >= settings.session_hourly_quota:
        st.warning(
            f"本小时提问次数已达上限（{settings.session_hourly_quota} 次），请稍后再试。"
        )
        return False

    timestamps.append(now)
    st.session_state["query_timestamps"] = timestamps
    return True
```

- [ ] **Step 2: Commit**

```bash
git add ui/auth.py
git commit -m "feat(ui): 访问码校验 + session 限流"
```

---

### Task 3: 实现 ui/trace.py（数据/图表/轨迹展示）

**Files:**
- Create: `ui/trace.py`

**Interfaces:**
- Consumes: trace 条目结构 `{"tool": str, "args": dict, "summary": str, "artifact": dict|None}`
- Produces:
  - `render_data(trace: list[dict])`：展示最新 DataFrame
  - `render_chart(trace: list[dict])`：展示最新 Plotly 图表
  - `render_trace(trace: list[dict])`：展示执行轨迹折叠卡片

- [ ] **Step 1: 实现 ui/trace.py**

```python
"""Agent trace side panel (data / chart / trace)."""

from __future__ import annotations

import streamlit as st


def _find_artifact(trace: list[dict], key: str) -> dict | None:
    """Find the last artifact containing *key* in trace."""
    for entry in reversed(trace):
        artifact = entry.get("artifact")
        if artifact and key in artifact:
            return artifact
    return None


def render_data(trace: list[dict]) -> None:
    """Display the latest query DataFrame."""
    artifact = _find_artifact(trace, "df")
    if artifact is None:
        st.info("暂无数据。提问数据相关问题后，查询结果将在此展示。")
        return

    df = artifact["df"]
    sql = artifact.get("sql", "")
    if sql:
        st.caption("SQL")
        st.code(sql, language="sql")
    st.caption(f"共 {len(df)} 行")
    st.dataframe(df, use_container_width=True)


def render_chart(trace: list[dict]) -> None:
    """Display the latest Plotly figure."""
    artifact = _find_artifact(trace, "figure")
    if artifact is None:
        st.info("暂无图表。提问需要可视化的问题后，图表将在此展示。")
        return

    fig = artifact["figure"]
    chart_type = artifact.get("chart_type", "")
    if chart_type:
        st.caption(f"图表类型: {chart_type}")
    st.plotly_chart(fig, use_container_width=True)


def render_trace(trace: list[dict]) -> None:
    """Display execution trace as collapsible cards."""
    if not trace:
        st.info("暂无执行轨迹。提问后，Agent 的思考过程将在此展示。")
        return

    for i, entry in enumerate(trace, 1):
        tool = entry.get("tool", "?")
        args = entry.get("args", {})
        summary = entry.get("summary", "")
        arg_str = ", ".join(f"{k}={v!r}" for k, v in args.items()) if args else ""

        with st.expander(f"[{i}] {tool}({arg_str})", expanded=False):
            st.text(summary)
```

- [ ] **Step 2: Commit**

```bash
git add ui/trace.py
git commit -m "feat(ui): 数据/图表/轨迹展示组件"
```

---

### Task 4: 实现 ui/chat.py（聊天组件）

**Files:**
- Create: `ui/chat.py`

**Interfaces:**
- Consumes: `agent.graph.run()`, `ui.auth.check_rate_limit()`
- Produces:
  - `render_chat()`：渲染聊天界面，处理用户输入，调用 agent

- [ ] **Step 1: 实现 ui/chat.py**

```python
"""Streamlit chat component."""

from __future__ import annotations

import streamlit as st

from agent.graph import run
from ui.auth import check_rate_limit


def _init_state() -> None:
    """Initialize session state for chat."""
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "last_result" not in st.session_state:
        st.session_state["last_result"] = None


def render_chat() -> None:
    """Render chat history + input. Call agent on user input."""
    _init_state()

    # 渲染历史消息
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("steps"):
                st.caption(f"执行步数: {msg['steps']}")

    # 输入框
    if prompt := st.chat_input("请输入问题…"):
        # 限流检查
        if not check_rate_limit():
            return

        # 渲染用户消息
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 调用 agent
        with st.chat_message("assistant"):
            with st.spinner("思考中…"):
                try:
                    result = run(prompt)
                except Exception as e:
                    st.error(f"执行出错: {e}")
                    st.session_state["messages"].append(
                        {"role": "assistant", "content": f"执行出错: {e}"}
                    )
                    return

            answer = result.get("answer", "")
            steps = result.get("steps", 0)
            st.markdown(answer)
            if steps:
                st.caption(f"执行步数: {steps}")

            # 存储结果
            st.session_state["messages"].append(
                {"role": "assistant", "content": answer, "steps": steps}
            )
            st.session_state["last_result"] = result

        # 触发右侧面板刷新
        st.rerun()
```

- [ ] **Step 2: Commit**

```bash
git add ui/chat.py
git commit -m "feat(ui): 聊天组件 + agent 调用"
```

---

### Task 5: 实现 app.py（入口整合）

**Files:**
- Modify: `app.py`（当前为脚手架）

**Interfaces:**
- Consumes: `ui.auth.check_access()`, `ui.chat.render_chat()`, `ui.trace.render_data/chart/trace`

- [ ] **Step 1: 重写 app.py**

```python
"""Streamlit entry point: auth gate + chat + trace panels."""

import streamlit as st

from ui.auth import check_access
from ui.chat import render_chat
from ui.trace import render_chart, render_data, render_trace


def main() -> None:
    st.set_page_config(
        page_title="Xiehaoyu-Agent",
        page_icon="🤖",
        layout="wide",
    )

    # 访问码校验
    if not check_access():
        return

    # 主页
    st.title("Xiehaoyu-Agent")
    st.caption("基于 LLM Agent 的个人智能体与 ChatBI 系统")

    col_chat, col_side = st.columns([3, 2])

    with col_chat:
        render_chat()

    with col_side:
        tab_data, tab_chart, tab_trace = st.tabs(["Data", "Chart", "Trace"])
        result = st.session_state.get("last_result")

        if result:
            trace = result.get("trace", [])
            with tab_data:
                render_data(trace)
            with tab_chart:
                render_chart(trace)
            with tab_trace:
                render_trace(trace)
        else:
            with tab_data:
                st.info("暂无数据。提问数据相关问题后，查询结果将在此展示。")
            with tab_chart:
                st.info("暂无图表。提问需要可视化的问题后，图表将在此展示。")
            with tab_trace:
                st.info("暂无执行轨迹。提问后，Agent 的思考过程将在此展示。")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 启动 Streamlit 验证无报错**

Run: `streamlit run app.py --server.headless true`
Expected: 启动无报错，浏览器打开显示访问码输入页

- [ ] **Step 3: 手动验证完整流程**

1. 输入访问码 `xhy2026`（从 .env 读取）→ 进入主页
2. 输入"介绍一下你自己" → 左侧显示回答，右侧 Trace Tab 显示 introduce_me 调用
3. 输入"2018年每月订单数，帮我画个图" → 左侧显示回答，右侧 Data Tab 显示 DataFrame，Chart Tab 显示折线图，Trace Tab 显示完整轨迹
4. 确认限流：连续提问多次后触发限流提示

- [ ] **Step 4: 运行 smoke_agent 确认 agent 层未被破坏**

Run: `python -m tests.smoke_agent`
Expected: "All cases passed."

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "feat(ui): Day 6 Streamlit UI 完整实现"
```
