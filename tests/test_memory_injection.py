"""记忆注入测试：planner 收到 [摘要+最近对话] 独立 user 消息（设计文档 §6）。"""

import os
os.environ["SKIP_CONFIG_VALIDATION"] = "1"  # 导入 agent.graph 前设置，防收集期 _validate() sys.exit

import asyncio
from types import SimpleNamespace

import agent.graph as graph
from agent import planner


class FakeClient:
    """捕获 messages 并回固定 JSON 的假 LLM client。"""

    def __init__(self, payload: str = '{"action": "finalize", "answer": "ok"}'):
        self.captured: list[dict] | None = None
        self._payload = payload
        outer = self

        class _Completions:
            def create(self, model, messages, temperature):
                outer.captured = messages
                return SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(content=outer._payload),
                            finish_reason="stop",
                        )
                    ]
                )

        self.chat = SimpleNamespace(completions=_Completions())


class TestPlannerInjection:
    def test_history_inserted_as_separate_user_message(self):
        client = FakeClient()
        planner.plan("后续问题", [], client=client, history_text="[会话摘要]\n聊了订单趋势")
        roles = [m["role"] for m in client.captured]
        assert roles == ["system", "user", "user"]
        assert "[会话摘要]" in client.captured[1]["content"]
        assert "【用户问题】" in client.captured[2]["content"]

    def test_no_history_keeps_two_messages(self):
        client = FakeClient()
        planner.plan("你好", [], client=client)
        assert [m["role"] for m in client.captured] == ["system", "user"]

    def test_history_passes_through_sanitize(self):
        """planner 自身不清洗 history_text（注入筛查在 build_history_text 完成，见 Task 6）；question 仍过。"""
        client = FakeClient()
        planner.plan("正常问题", [], client=client, history_text="[最近对话]\n用户: 你好")
        assert "[最近对话]" in client.captured[1]["content"]


class TestGraphWiring:
    def test_run_passes_history_to_planner(self, monkeypatch):
        captured = {}

        def fake_plan(question, trace, client=None, history_text=""):
            captured["history_text"] = history_text
            return {"action": "finalize", "answer": "ok"}

        monkeypatch.setattr(graph, "plan", fake_plan)
        result = graph.run("问题", history_text="[会话摘要]\nabc")
        assert captured["history_text"] == "[会话摘要]\nabc"
        assert result["answer"] == "ok"

    def test_run_default_history_empty(self, monkeypatch):
        captured = {}

        def fake_plan(question, trace, client=None, history_text=""):
            captured["history_text"] = history_text
            return {"action": "finalize", "answer": "ok"}

        monkeypatch.setattr(graph, "plan", fake_plan)
        graph.run("问题")
        assert captured["history_text"] == ""

    def test_final_answer_event_steps_not_zero(self, monkeypatch):
        """finalize_node 补 step 后，SSE final_answer 事件的 steps 反映真实步数。"""

        def fake_plan(question, trace, client=None, history_text=""):
            return {"action": "finalize", "answer": "ok"}

        monkeypatch.setattr(graph, "plan", fake_plan)

        async def collect():
            return [e async for e in graph.stream_run("问题")]

        events = asyncio.run(collect())
        final = next(e for e in events if e["type"] == "final_answer")
        assert final["data"]["steps"] == 1  # planner 跑了一步