"""Smoke test for the full Agent orchestration (Day 5).

验证 3 类问题：
  1. 纯介绍 — planner → introduce_me → finalize
  2. 纯查数 — planner → query_data → visualize → explain_result → finalize
  3. 混合   — planner → introduce_me → query_data → ... → finalize

用法：
    python -m tests.smoke_agent
"""

from __future__ import annotations

from agent.graph import run

CASES = [
    "介绍一下你自己",
    "2018 年每月订单数，帮我画个图并解读一下",
    "你了解电商数据吗？给我看一下 olist 的月订单趋势",
]


def main() -> None:
    for i, question in enumerate(CASES, 1):
        print(f"\n{'='*60}")
        print(f"Case {i}: {question}")
        print(f"{'='*60}")

        result = run(question)

        print(f"\n--- 执行轨迹 ({result['steps']} 步) ---")
        for j, t in enumerate(result["trace"], 1):
            print(f"  [{j}] {t['tool']}({t['args']})")
            summary = t["summary"][:200]
            print(f"      → {summary}{'...' if len(t['summary']) > 200 else ''}")

        print(f"\n--- 最终回答 ---")
        print(result["answer"])

    print(f"\n{'='*60}")
    print("All cases passed.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
