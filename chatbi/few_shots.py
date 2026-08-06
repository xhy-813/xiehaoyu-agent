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
    {
        # 明确示范 order_reviews 表的两种计数场景：
        # - 统计评价条数 → COUNT(*)
        # - 统计有评价的订单数 → COUNT(DISTINCT order_id)
        "q": "评分为 5 分的评价一共有多少条（每条评价算一条）",
        "sql": (
            "SELECT COUNT(*) AS review_cnt "
            "FROM order_reviews "
            "WHERE review_score = 5;"
        ),
    },
    {
        "q": "2017 年和 2018 年各自的订单数（每年一行，按年份升序）",
        "sql": (
            "SELECT strftime('%Y', order_purchase_timestamp) AS year, "
            "COUNT(*) AS order_cnt "
            "FROM orders "
            "WHERE order_purchase_timestamp LIKE '2017%' "
            "   OR order_purchase_timestamp LIKE '2018%' "
            "GROUP BY year ORDER BY year;"
        ),
    },
    {
        # order_reviews 表中统计"订单数"→ COUNT(DISTINCT order_id)
        # 一笔订单可能有多条评价行，需要去重
        "q": "评分为 5 分的订单有多少笔？",
        "sql": (
            "SELECT COUNT(DISTINCT order_id) AS order_cnt "
            "FROM order_reviews "
            "WHERE review_score = 5;"
        ),
    },
    {
        # 同时查询销量、收入、平均评分时，JOIN order_reviews 用 INNER JOIN
        # 保证只统计有评价的订单，item_cnt/revenue/avg_score 口径一致
        "q": "各英文品类的销量、总收入和平均评分 top 5",
        "sql": (
            "SELECT ct.product_category_name_english AS category, "
            "COUNT(oi.order_item_id) AS item_cnt, "
            "ROUND(SUM(oi.price), 2) AS revenue, "
            "ROUND(AVG(r.review_score), 4) AS avg_score "
            "FROM order_items oi "
            "JOIN products p ON p.product_id = oi.product_id "
            "JOIN category_translation ct "
            "  ON ct.product_category_name = p.product_category_name "
            "JOIN order_reviews r ON r.order_id = oi.order_id "
            "GROUP BY category "
            "ORDER BY revenue DESC "
            "LIMIT 5;"
        ),
    },
    {
        # "A vs B" → 宽表，每行一个时间维度，两列分别是两个度量
        # 不要输出长表（customer_type 列）
        "q": "2018 年每月的新客户数 vs 复购客户数（每月一行，两列分别是 first_time_customers 和 repeat_customers）",
        "sql": (
            "WITH first_month AS ("
            "  SELECT c.customer_unique_id, "
            "         strftime('%Y-%m', MIN(o.order_purchase_timestamp)) AS fm "
            "  FROM customers c JOIN orders o ON o.customer_id = c.customer_id "
            "  GROUP BY c.customer_unique_id"
            "), active AS ("
            "  SELECT strftime('%Y-%m', o.order_purchase_timestamp) AS month, "
            "         c.customer_unique_id "
            "  FROM customers c JOIN orders o ON o.customer_id = c.customer_id "
            "  WHERE o.order_purchase_timestamp LIKE '2018%' "
            "  GROUP BY month, c.customer_unique_id"
            ") "
            "SELECT a.month, "
            "  COUNT(CASE WHEN a.month = f.fm THEN 1 END) AS first_time_customers, "
            "  COUNT(CASE WHEN a.month > f.fm THEN 1 END) AS repeat_customers "
            "FROM active a JOIN first_month f ON f.customer_unique_id = a.customer_unique_id "
            "GROUP BY a.month ORDER BY a.month;"
        ),
    },
]


def format_few_shots(shots: list[dict] | None = None) -> str:
    shots = shots or FEW_SHOTS
    parts = []
    for i, s in enumerate(shots, 1):
        parts.append(f"示例 {i}\nQ: {s['q']}\nA: {s['sql']}")
    return "\n\n".join(parts)
