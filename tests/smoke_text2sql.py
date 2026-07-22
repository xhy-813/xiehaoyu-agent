"""Ad-hoc manual test for Day 2 Text2SQL.

跑 5 个问题，输出 SQL + 前若干行结果 + 尝试次数。
"""

from agent.tools.query_data import query_data


CASES = [
    "2018 年每月的订单数",
    "支付方式分布（按订单数）",
    "销量 top 5 的商品品类，用英文品类名",
    "各州（customer_state）的下单客户数 top 10",
    "已送达（delivered）订单的平均评分",
]


def main() -> None:
    for i, q in enumerate(CASES, 1):
        print(f"\n===== Case {i}: {q} =====")
        try:
            r = query_data(q)
        except Exception as e:  # noqa: BLE001
            print("FAILED:", e)
            continue
        print(f"attempts={r.attempts}  elapsed_ms={r.elapsed_ms}")
        print("SQL:", r.sql)
        print("rows:", len(r.df))
        print(r.df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
