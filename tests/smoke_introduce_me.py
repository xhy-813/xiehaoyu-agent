"""Smoke test for Day 4 RAG introduce_me tool."""

from agent.tools.introduce_me import introduce_me


CASES = [
    "介绍一下你自己",
    "你 K12 数仓项目做了什么？用了哪些技术？",
    "你在龙腾出行实习期间主要负责什么工作？",
    "你申请的目标岗位是什么？技术栈有哪些？",
]


def main() -> None:
    for i, q in enumerate(CASES, 1):
        print(f"\n===== Case {i}: {q} =====")
        r = introduce_me(q, top_k=5)
        print("--- 引用 ---")
        for j, c in enumerate(r.citations, 1):
            print(f"[{j}] {c['source']}  # {c['heading']}  (dist={c['distance']}, sim={c['similarity']})")
        print("--- 回答 ---")
        print(r.answer)


if __name__ == "__main__":
    main()
