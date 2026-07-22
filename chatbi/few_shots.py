"""Few-shot (question, SQL) pairs for Text2SQL prompt.

Kept small, high-quality, and covering: 时间过滤 / 聚合 / 排序 top-N / join / 分类翻译。
"""

from __future__ import annotations

FEW_SHOTS: list[dict] = [
    {
        "q": "2018 年每月的订单数",
        "sql": (
            "SELECT strftime('%Y-%m', order_purchase_timestamp) AS month, "
            "COUNT(*) AS order_cnt "
            "FROM orders "
            "WHERE order_purchase_timestamp LIKE '2018%' "
            "GROUP BY month ORDER BY month;"
        ),
    },
    {
        "q": "支付方式的分布（订单数）",
        "sql": (
            "SELECT payment_type, COUNT(DISTINCT order_id) AS order_cnt "
            "FROM order_payments "
            "GROUP BY payment_type ORDER BY order_cnt DESC;"
        ),
    },
    {
        "q": "销量 top 5 的商品品类（用英文品类名）",
        "sql": (
            "SELECT ct.product_category_name_english AS category, "
            "COUNT(*) AS item_cnt "
            "FROM order_items oi "
            "JOIN products p ON p.product_id = oi.product_id "
            "JOIN category_translation ct "
            "  ON ct.product_category_name = p.product_category_name "
            "GROUP BY category "
            "ORDER BY item_cnt DESC "
            "LIMIT 5;"
        ),
    },
    {
        "q": "各州（customer_state）的下单客户数 top 10",
        "sql": (
            "SELECT c.customer_state, "
            "COUNT(DISTINCT c.customer_unique_id) AS customer_cnt "
            "FROM customers c "
            "JOIN orders o ON o.customer_id = c.customer_id "
            "GROUP BY c.customer_state "
            "ORDER BY customer_cnt DESC "
            "LIMIT 10;"
        ),
    },
    {
        "q": "已送达订单的平均评分",
        "sql": (
            "SELECT AVG(r.review_score) AS avg_score "
            "FROM order_reviews r "
            "JOIN orders o ON o.order_id = r.order_id "
            "WHERE o.order_status = 'delivered';"
        ),
    },
]


def format_few_shots(shots: list[dict] | None = None) -> str:
    shots = shots or FEW_SHOTS
    parts = []
    for i, s in enumerate(shots, 1):
        parts.append(f"示例 {i}\nQ: {s['q']}\nA: {s['sql']}")
    return "\n\n".join(parts)
