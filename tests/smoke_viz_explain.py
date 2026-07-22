"""Smoke test for Day 3: visualize + explain over 4 shapes of results."""

from __future__ import annotations

import pandas as pd

from agent.tools.explain_result import explain_result
from agent.tools.visualize import visualize


CASES = [
    (
        "已送达订单的平均评分",
        "SELECT AVG(review_score) AS avg_score FROM order_reviews;",
        pd.DataFrame({"avg_score": [4.156]}),
    ),
    (
        "支付方式分布（按订单数）",
        "SELECT payment_type, COUNT(DISTINCT order_id) AS order_cnt FROM order_payments GROUP BY payment_type ORDER BY order_cnt DESC;",
        pd.DataFrame(
            {
                "payment_type": ["credit_card", "boleto", "voucher", "debit_card", "not_defined"],
                "order_cnt": [76505, 19784, 3866, 1528, 3],
            }
        ),
    ),
    (
        "2018 年每月订单数",
        "SELECT strftime('%Y-%m', order_purchase_timestamp) AS month, COUNT(*) AS order_cnt FROM orders WHERE order_purchase_timestamp LIKE '2018%' GROUP BY month ORDER BY month;",
        pd.DataFrame(
            {
                "month": [f"2018-{m:02d}" for m in range(1, 9)],
                "order_cnt": [7269, 6728, 7211, 6939, 6873, 6167, 6292, 6512],
            }
        ),
    ),
    (
        "商品重量与价格的关系",
        "SELECT product_weight_g, price FROM order_items JOIN products USING(product_id) LIMIT 500;",
        pd.DataFrame(
            {
                "product_weight_g": [100, 250, 500, 1000, 2000, 5000],
                "price": [10.5, 25.0, 45.0, 80.0, 150.0, 300.0],
            }
        ),
    ),
]


def main() -> None:
    for i, (q, sql, df) in enumerate(CASES, 1):
        print(f"\n===== Case {i}: {q} =====")
        viz = visualize(df, q)
        print(f"chart_type={viz.chart_type}  reason={viz.reason}")
        insight = explain_result(q, sql, df)
        print("INSIGHT:")
        print(insight)


if __name__ == "__main__":
    main()
