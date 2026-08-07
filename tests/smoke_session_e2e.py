"""会话持久化端到端冒烟（设计文档 §11）。

新建 → 提问 → 追问（验证记忆注入）→ 回放（验证消息 + 图表 trace 完整）。
走真实 Agent + 真实 LLM，需要 .env 里的 DEEPSEEK_API_KEY。
注意：会在本地创建/复用 data/sessions.db（已被 .gitignore 忽略）。

用法：
    python -m tests.smoke_session_e2e
"""

from __future__ import annotations

import json
import uuid

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services import session_store


def main() -> None:
    session_store.init_store()
    client = TestClient(app)
    headers = {"X-User-Id": str(uuid.uuid4())}

    # 1. 新建会话
    resp = client.post("/api/sessions", headers=headers)
    assert resp.status_code == 200, resp.text
    sid = resp.json()["session_id"]
    print(f"[1] 新建会话: {sid}")

    # 2. 第一轮提问
    q1 = "2018 年订单量最高的月份是几月？"
    resp = client.post("/api/chat", json={"question": q1, "session_id": sid}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert "final_answer" in resp.text
    print(f"[2] 第一轮提问完成: {q1}")

    # 3. 追问（依赖上文 → 验证记忆注入路径不报错）
    q2 = "那 2017 年同月份呢？"
    resp = client.post("/api/chat", json={"question": q2, "session_id": sid}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert "final_answer" in resp.text
    print(f"[3] 追问完成: {q2}")

    # 4. 回放
    resp = client.get(f"/api/sessions/{sid}", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    msgs = body["messages"]
    assert len(msgs) == 4, f"期望 4 条消息，实际 {len(msgs)}"
    assistant = [m for m in msgs if m["role"] == "assistant"]
    assert all(m["content"] for m in assistant), "assistant 消息内容为空"
    with_trace = [m for m in assistant if m["trace"]]
    print(f"[4] 回放: {len(msgs)} 条消息，{len(with_trace)} 条带执行轨迹")
    for m in with_trace:
        for step in m["trace"]:
            art = step.get("artifact") or {}
            if "df_json" in art:
                json.loads(art["df_json"])  # 必须可解析（字符串保真）
            if "figure_json" in art:
                json.loads(art["figure_json"])

    # 5. 列表 + 标题
    resp = client.get("/api/sessions", headers=headers)
    item = next(s for s in resp.json()["sessions"] if s["id"] == sid)
    print(f"[5] 列表标题: {item['title']!r}（异步生成，可能仍为 None → 前端显示'新会话'）")

    print("\n" + "=" * 60)
    print("Smoke session e2e passed.")
    print("=" * 60)


if __name__ == "__main__":
    main()