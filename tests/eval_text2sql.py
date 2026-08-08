"""Text2SQL 基线准确率评测（50 题）。

评测方式：执行准确率（Execution Accuracy）
    - 用 gold SQL 和模型 SQL 分别查真实 olist.db
    - 对比结果 DataFrame 是否等价（忽略行列顺序）
    - 只要结果等价即算通过，不要求 SQL 字面一致

运行方式：
    python -m tests.eval_text2sql
    python -m tests.eval_text2sql --verbose
    python -m tests.eval_text2sql --level easy      # 只跑 easy
    python -m tests.eval_text2sql --level medium
    python -m tests.eval_text2sql --level hard

需要真实 LLM API Key（DEEPSEEK_API_KEY），以及 chatbi/data/olist.db。
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# ── 路径设置（支持直接 python tests/eval_text2sql.py 运行）──
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agent.tools.query_data import query_data, _get_engine  # noqa: E402

DB_PATH = _ROOT / "chatbi" / "data" / "olist.db"


# ═══════════════════════════════════════════════════════════════
# 50 道评测题（简单 20 + 中等 20 + 复杂 10）
# ═══════════════════════════════════════════════════════════════

EVAL_CASES: list[dict] = [
    # ────────────────────────────────────────────────
    # EASY（20 题）：单表 or 简单过滤/聚合，无复杂 JOIN
    # ────────────────────────────────────────────────
    {
        "id": "E01",
        "level": "easy",
        "question": "订单总数是多少？",
        "gold_sql": "SELECT COUNT(*) AS order_cnt FROM orders;",
    },
    {
        "id": "E02",
        "level": "easy",
        "question": "独立客户（自然人）总数是多少？",
        "gold_sql": "SELECT COUNT(DISTINCT customer_unique_id) AS customer_cnt FROM customers;",
    },
    {
        "id": "E03",
        "level": "easy",
        "question": "各种订单状态分别有多少笔？",
        "gold_sql": (
            "SELECT order_status, COUNT(*) AS cnt "
            "FROM orders GROUP BY order_status ORDER BY cnt DESC;"
        ),
    },
    {
        "id": "E04",
        "level": "easy",
        "question": "2018 年的订单总数",
        "gold_sql": (
            "SELECT COUNT(*) AS order_cnt FROM orders "
            "WHERE order_purchase_timestamp LIKE '2018%';"
        ),
    },
    {
        "id": "E05",
        "level": "easy",
        "question": "所有订单的平均评分是多少？",
        "gold_sql": "SELECT ROUND(AVG(review_score), 4) AS avg_score FROM order_reviews;",
    },
    {
        "id": "E06",
        "level": "easy",
        "question": "用信用卡（credit_card）支付的订单有多少笔？",
        "gold_sql": (
            "SELECT COUNT(DISTINCT order_id) AS cnt FROM order_payments "
            "WHERE payment_type = 'credit_card';"
        ),
    },
    {
        "id": "E07",
        "level": "easy",
        "question": "已取消（canceled）的订单数量",
        "gold_sql": (
            "SELECT COUNT(*) AS cnt FROM orders WHERE order_status = 'canceled';"
        ),
    },
    {
        "id": "E08",
        "level": "easy",
        # 808 审查 H3 换题（原题与 few_shot#8 重叠）：不同商品数去重统计
        "question": "order_items 表里一共有多少个不同的商品（product_id）？",
        "gold_sql": (
            "SELECT COUNT(DISTINCT product_id) AS cnt FROM order_items;"
        ),
    },
    {
        "id": "E09",
        "level": "easy",
        "question": "SP 州的客户数（customer_id 维度）",
        "gold_sql": (
            "SELECT COUNT(*) AS cnt FROM customers WHERE customer_state = 'SP';"
        ),
    },
    {
        "id": "E10",
        "level": "easy",
        "question": "2017 年的订单总数",
        "gold_sql": (
            "SELECT COUNT(*) AS order_cnt FROM orders "
            "WHERE order_purchase_timestamp LIKE '2017%';"
        ),
    },
    {
        "id": "E11",
        "level": "easy",
        "question": "所有订单商品的运费（freight_value）总和",
        "gold_sql": "SELECT ROUND(SUM(freight_value), 2) AS total_freight FROM order_items;",
    },
    {
        "id": "E12",
        "level": "easy",
        "question": "products 表中共有多少个不同的商品品类（葡萄牙语）？",
        "gold_sql": (
            "SELECT COUNT(DISTINCT product_category_name) AS cnt FROM products;"
        ),
    },
    {
        "id": "E13",
        "level": "easy",
        "question": "各种支付方式的平均支付金额（保留 2 位小数）",
        "gold_sql": (
            "SELECT payment_type, ROUND(AVG(payment_value), 2) AS avg_value "
            "FROM order_payments GROUP BY payment_type ORDER BY avg_value DESC;"
        ),
    },
    {
        "id": "E14",
        "level": "easy",
        "question": "卖家分布在哪些州？每州有多少卖家？",
        "gold_sql": (
            "SELECT seller_state, COUNT(DISTINCT seller_id) AS seller_cnt "
            "FROM sellers GROUP BY seller_state ORDER BY seller_cnt DESC;"
        ),
    },
    {
        "id": "E15",
        "level": "easy",
        "question": "使用分期付款（installments > 1）的支付记录有多少条？",
        "gold_sql": (
            "SELECT COUNT(*) AS cnt FROM order_payments WHERE payment_installments > 1;"
        ),
    },
    {
        "id": "E16",
        "level": "easy",
        "question": "平均每笔订单包含多少件商品？（保留 2 位小数）",
        "gold_sql": (
            "SELECT ROUND(AVG(item_cnt), 2) AS avg_items "
            "FROM (SELECT order_id, COUNT(*) AS item_cnt FROM order_items GROUP BY order_id);"
        ),
    },
    {
        "id": "E17",
        "level": "easy",
        "question": "有评论（order_reviews 里有记录）的订单数",
        "gold_sql": (
            "SELECT COUNT(DISTINCT order_id) AS cnt FROM order_reviews;"
        ),
    },
    {
        "id": "E18",
        "level": "easy",
        "question": "订单商品表（order_items）里最高的单件商品价格是多少？",
        "gold_sql": "SELECT MAX(price) AS max_price FROM order_items;",
    },
    {
        "id": "E19",
        "level": "easy",
        "question": "已送达（delivered）的订单数",
        "gold_sql": (
            "SELECT COUNT(*) AS cnt FROM orders WHERE order_status = 'delivered';"
        ),
    },
    {
        "id": "E20",
        "level": "easy",
        "question": "boleto 支付方式一共支付了多少金额？（保留 2 位小数）",
        "gold_sql": (
            "SELECT ROUND(SUM(payment_value), 2) AS total "
            "FROM order_payments WHERE payment_type = 'boleto';"
        ),
    },

    # ────────────────────────────────────────────────
    # MEDIUM（20 题）：多表 JOIN、分组聚合、时间运算
    # ────────────────────────────────────────────────
    {
        "id": "M01",
        "level": "medium",
        # 808 审查 H3 换题（原题与 few_shot#1 重叠）：周粒度时间分组。
        # gold 修订：周数输出为整数（原 gold 的 '01' 零填充字符串是纯格式伪差异，
        # 模型答案数值完全一致却判 FAIL）
        "question": "2018 年每周的订单数（按周数升序）",
        "gold_sql": (
            "SELECT CAST(strftime('%W', order_purchase_timestamp) AS INTEGER) AS week, "
            "COUNT(*) AS order_cnt "
            "FROM orders WHERE order_purchase_timestamp LIKE '2018%' "
            "GROUP BY week ORDER BY week;"
        ),
    },
    {
        "id": "M02",
        "level": "medium",
        # 808 审查 H3 换题（原题与 few_shot#3 重叠）：评分过滤 + 品类 top-N
        "question": "评分 4 分及以上订单数最多的 5 个商品品类（英文名，按订单数降序）",
        "gold_sql": (
            "SELECT ct.product_category_name_english AS category, "
            "COUNT(DISTINCT oi.order_id) AS order_cnt "
            "FROM order_items oi "
            "JOIN products p ON p.product_id = oi.product_id "
            "JOIN category_translation ct ON ct.product_category_name = p.product_category_name "
            "JOIN order_reviews r ON r.order_id = oi.order_id "
            "WHERE r.review_score >= 4 "
            "GROUP BY category ORDER BY order_cnt DESC LIMIT 5;"
        ),
    },
    {
        "id": "M03",
        "level": "medium",
        # 808 审查 H3 换题（原题与 few_shot#4 重叠）：城市维度卖家分布
        "question": "卖家数量最多的 10 个城市（seller_city，按卖家数降序）",
        "gold_sql": (
            "SELECT seller_city, COUNT(DISTINCT seller_id) AS seller_cnt "
            "FROM sellers GROUP BY seller_city ORDER BY seller_cnt DESC LIMIT 10;"
        ),
    },
    {
        "id": "M04",
        "level": "medium",
        # 808 审查 H3 换题（原题与 few_shot#5 重叠）：品类运费均值 top-1
        "question": "平均运费（freight_value 均值，保留 2 位小数）最高的商品品类是哪个（英文名）？",
        "gold_sql": (
            "SELECT ct.product_category_name_english AS category, "
            "ROUND(AVG(oi.freight_value), 2) AS avg_freight "
            "FROM order_items oi "
            "JOIN products p ON p.product_id = oi.product_id "
            "JOIN category_translation ct ON ct.product_category_name = p.product_category_name "
            "GROUP BY category ORDER BY avg_freight DESC LIMIT 1;"
        ),
    },
    {
        "id": "M05",
        "level": "medium",
        "question": "收入（price 之和）最高的 5 个商品品类（英文名）",
        "gold_sql": (
            "SELECT ct.product_category_name_english AS category, "
            "ROUND(SUM(oi.price), 2) AS revenue "
            "FROM order_items oi "
            "JOIN products p ON p.product_id = oi.product_id "
            "JOIN category_translation ct ON ct.product_category_name = p.product_category_name "
            "GROUP BY category ORDER BY revenue DESC LIMIT 5;"
        ),
    },
    {
        "id": "M06",
        "level": "medium",
        "question": "2018 年各季度的订单数（Q1/Q2/Q3/Q4）",
        "gold_sql": (
            "SELECT CASE "
            "  WHEN strftime('%m', order_purchase_timestamp) BETWEEN '01' AND '03' THEN 'Q1' "
            "  WHEN strftime('%m', order_purchase_timestamp) BETWEEN '04' AND '06' THEN 'Q2' "
            "  WHEN strftime('%m', order_purchase_timestamp) BETWEEN '07' AND '09' THEN 'Q3' "
            "  ELSE 'Q4' END AS quarter, "
            "COUNT(*) AS order_cnt "
            "FROM orders WHERE order_purchase_timestamp LIKE '2018%' "
            "GROUP BY quarter ORDER BY quarter;"
        ),
    },
    {
        "id": "M07",
        "level": "medium",
        # "订单数" → 去重统计 order_id
        "question": "评分 1~5 各分数段的订单数分布",
        "gold_sql": (
            "SELECT review_score, COUNT(DISTINCT order_id) AS order_cnt "
            "FROM order_reviews GROUP BY review_score ORDER BY review_score;"
        ),
    },
    {
        "id": "M08",
        "level": "medium",
        "question": "每个卖家的总销售额（price 之和）top 10（保留 2 位小数）",
        "gold_sql": (
            "SELECT seller_id, ROUND(SUM(price), 2) AS revenue "
            "FROM order_items GROUP BY seller_id ORDER BY revenue DESC LIMIT 10;"
        ),
    },
    {
        "id": "M09",
        "level": "medium",
        "question": "已送达订单从下单到实际送达的平均天数（保留 2 位小数）",
        "gold_sql": (
            "SELECT ROUND(AVG("
            "  (julianday(order_delivered_customer_date) - julianday(order_purchase_timestamp))"
            "), 2) AS avg_days "
            "FROM orders "
            "WHERE order_status = 'delivered' "
            "  AND order_delivered_customer_date IS NOT NULL "
            "  AND order_purchase_timestamp IS NOT NULL;"
        ),
    },
    {
        "id": "M10",
        "level": "medium",
        "question": "信用卡分期付款的平均分期数（installments > 1，保留 2 位小数）",
        "gold_sql": (
            "SELECT ROUND(AVG(payment_installments), 2) AS avg_installments "
            "FROM order_payments "
            "WHERE payment_type = 'credit_card' AND payment_installments > 1;"
        ),
    },
    {
        "id": "M11",
        "level": "medium",
        "question": "2018 年 Q1（1~3 月）每月的 GMV（商品总售价，保留 2 位小数）",
        "gold_sql": (
            "SELECT strftime('%Y-%m', o.order_purchase_timestamp) AS month, "
            "ROUND(SUM(oi.price), 2) AS gmv "
            "FROM orders o JOIN order_items oi ON oi.order_id = o.order_id "
            "WHERE o.order_purchase_timestamp LIKE '2018-0%' "
            "  AND strftime('%m', o.order_purchase_timestamp) IN ('01','02','03') "
            "GROUP BY month ORDER BY month;"
        ),
    },
    {
        "id": "M12",
        "level": "medium",
        "question": "各州卖家的平均单件商品价格 top 10（保留 2 位小数）",
        "gold_sql": (
            "SELECT s.seller_state, ROUND(AVG(oi.price), 2) AS avg_price "
            "FROM order_items oi JOIN sellers s ON s.seller_id = oi.seller_id "
            "GROUP BY s.seller_state ORDER BY avg_price DESC LIMIT 10;"
        ),
    },
    {
        "id": "M13",
        "level": "medium",
        "question": "购买次数最多的 top 10 客户（按 customer_unique_id 统计订单数）",
        "gold_sql": (
            "SELECT c.customer_unique_id, COUNT(o.order_id) AS order_cnt "
            "FROM customers c JOIN orders o ON o.customer_id = c.customer_id "
            "GROUP BY c.customer_unique_id ORDER BY order_cnt DESC LIMIT 10;"
        ),
    },
    {
        "id": "M14",
        "level": "medium",
        "question": "运费占商品总价比例最高的 5 个品类（英文名，保留 4 位小数）",
        "gold_sql": (
            "SELECT ct.product_category_name_english AS category, "
            "ROUND(SUM(oi.freight_value) / SUM(oi.price), 4) AS freight_ratio "
            "FROM order_items oi "
            "JOIN products p ON p.product_id = oi.product_id "
            "JOIN category_translation ct ON ct.product_category_name = p.product_category_name "
            "GROUP BY category ORDER BY freight_ratio DESC LIMIT 5;"
        ),
    },
    {
        "id": "M15",
        "level": "medium",
        "question": "各州（customer_state）的平均订单金额（商品 price 之和，不含运费，保留 2 位小数）top 10",
        "gold_sql": (
            "SELECT c.customer_state, ROUND(AVG(oi_sum.total), 2) AS avg_order_value "
            "FROM orders o "
            "JOIN customers c ON c.customer_id = o.customer_id "
            "JOIN (SELECT order_id, SUM(price) AS total FROM order_items GROUP BY order_id) oi_sum "
            "  ON oi_sum.order_id = o.order_id "
            "GROUP BY c.customer_state ORDER BY avg_order_value DESC LIMIT 10;"
        ),
    },
    {
        "id": "M16",
        "level": "medium",
        "question": "下单到付款审核（order_approved_at）的平均时长（小时，保留 2 位小数）",
        "gold_sql": (
            "SELECT ROUND(AVG("
            "  (julianday(order_approved_at) - julianday(order_purchase_timestamp)) * 24"
            "), 2) AS avg_hours "
            "FROM orders "
            "WHERE order_approved_at IS NOT NULL AND order_purchase_timestamp IS NOT NULL;"
        ),
    },
    {
        "id": "M17",
        "level": "medium",
        "question": "每个支付方式的订单数和总支付金额（保留 2 位小数）",
        "gold_sql": (
            "SELECT payment_type, "
            "COUNT(DISTINCT order_id) AS order_cnt, "
            "ROUND(SUM(payment_value), 2) AS total_paid "
            "FROM order_payments GROUP BY payment_type ORDER BY order_cnt DESC;"
        ),
    },
    {
        "id": "M18",
        "level": "medium",
        # "订单数" → 分子分母都按 order_id 去重
        "question": "有留言评论（review_comment_message 不为空）的订单数占总评价订单数的比例（保留 4 位小数）",
        "gold_sql": (
            "SELECT ROUND("
            "  1.0 * COUNT(DISTINCT CASE WHEN review_comment_message IS NOT NULL "
            "                             AND review_comment_message != '' "
            "                             THEN order_id END) "
            "  / COUNT(DISTINCT order_id), 4) AS ratio "
            "FROM order_reviews;"
        ),
    },
    {
        "id": "M19",
        "level": "medium",
        # 输出 seller_id + avg_score（不强制要求 order_cnt，evaluator 按值比较忽略列名）
        "question": "每个卖家的平均评分（只含有评论的订单，保留 4 位小数）top 10（按评分降序，至少 10 笔订单）",
        "gold_sql": (
            "SELECT oi.seller_id, ROUND(AVG(r.review_score), 4) AS avg_score, "
            "COUNT(DISTINCT o.order_id) AS order_cnt "
            "FROM order_items oi "
            "JOIN orders o ON o.order_id = oi.order_id "
            "JOIN order_reviews r ON r.order_id = o.order_id "
            "GROUP BY oi.seller_id "
            "HAVING COUNT(DISTINCT o.order_id) >= 10 "
            "ORDER BY avg_score DESC LIMIT 10;"
        ),
    },
    {
        "id": "M20",
        "level": "medium",
        # 808 审查 H3 换题（原题与 few_shot#7 重叠）：年度 GMV 对比
        "question": "2017 年和 2018 年各自的 GMV（商品 price 之和，每年一行，保留 2 位小数）",
        "gold_sql": (
            "SELECT strftime('%Y', o.order_purchase_timestamp) AS year, "
            "ROUND(SUM(oi.price), 2) AS gmv "
            "FROM orders o JOIN order_items oi ON oi.order_id = o.order_id "
            "WHERE o.order_purchase_timestamp LIKE '2017%' OR o.order_purchase_timestamp LIKE '2018%' "
            "GROUP BY year ORDER BY year;"
        ),
    },

    # ────────────────────────────────────────────────
    # HARD（10 题）：CTE、子查询、复杂业务逻辑
    # ────────────────────────────────────────────────
    {
        "id": "H01",
        "level": "hard",
        "question": "复购率：购买过 2 次及以上的客户占所有有购买记录客户的比例（保留 4 位小数）",
        "gold_sql": (
            "WITH order_cnt AS ("
            "  SELECT c.customer_unique_id, COUNT(o.order_id) AS cnt "
            "  FROM customers c JOIN orders o ON o.customer_id = c.customer_id "
            "  GROUP BY c.customer_unique_id"
            ") "
            "SELECT ROUND(1.0 * SUM(CASE WHEN cnt >= 2 THEN 1 ELSE 0 END) / COUNT(*), 4) AS repurchase_rate "
            "FROM order_cnt;"
        ),
    },
    {
        "id": "H02",
        "level": "hard",
        "question": "2018 年每月 GMV（商品总售价）及与上月相比的环比增长率（保留 4 位小数，无上月则为 NULL）",
        "gold_sql": (
            "WITH monthly AS ("
            "  SELECT strftime('%Y-%m', o.order_purchase_timestamp) AS month, "
            "         ROUND(SUM(oi.price), 2) AS gmv "
            "  FROM orders o JOIN order_items oi ON oi.order_id = o.order_id "
            "  WHERE o.order_purchase_timestamp LIKE '2018%' "
            "  GROUP BY month"
            "), "
            "with_prev AS ("
            "  SELECT month, gmv, "
            "         LAG(gmv) OVER (ORDER BY month) AS prev_gmv "
            "  FROM monthly"
            ") "
            "SELECT month, gmv, "
            "  CASE WHEN prev_gmv IS NOT NULL "
            "       THEN ROUND((gmv - prev_gmv) / prev_gmv, 4) "
            "       ELSE NULL END AS mom_growth "
            "FROM with_prev ORDER BY month;"
        ),
    },
    {
        "id": "H03",
        "level": "hard",
        # 808 审查 H3 换题（原题与 few_shot#9 重叠）：客户分群人均消费对比。
        # 首跑失败后题面消歧：指定金额口径（price 之和）与输出列名/取值，
        # 与 H07 显式指定输出列的既有风格一致
        "question": (
            "复购客户（购买 2 次及以上）与一次性客户的人均消费金额（按商品 price 之和计算）"
            "分别是多少（保留 2 位小数）？输出两列：customer_type（取值 repeat / one_time）、avg_spend"
        ),
        "gold_sql": (
            "WITH cust AS ("
            "  SELECT c.customer_unique_id, "
            "         COUNT(DISTINCT o.order_id) AS order_cnt, "
            "         SUM(oi.price) AS total_spend "
            "  FROM customers c "
            "  JOIN orders o ON o.customer_id = c.customer_id "
            "  JOIN order_items oi ON oi.order_id = o.order_id "
            "  GROUP BY c.customer_unique_id"
            ") "
            "SELECT CASE WHEN order_cnt >= 2 THEN 'repeat' ELSE 'one_time' END AS customer_type, "
            "ROUND(AVG(total_spend), 2) AS avg_spend "
            "FROM cust GROUP BY customer_type ORDER BY customer_type;"
        ),
    },
    {
        "id": "H04",
        "level": "hard",
        "question": "配送超时（实际送达晚于预计送达）的订单比例（按州统计，取超时率最高的 10 个州，保留 4 位小数）",
        "gold_sql": (
            "SELECT c.customer_state, "
            "ROUND(1.0 * SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date "
            "                     THEN 1 ELSE 0 END) / COUNT(*), 4) AS late_rate "
            "FROM orders o JOIN customers c ON c.customer_id = o.customer_id "
            "WHERE o.order_status = 'delivered' "
            "  AND o.order_delivered_customer_date IS NOT NULL "
            "  AND o.order_estimated_delivery_date IS NOT NULL "
            "GROUP BY c.customer_state HAVING COUNT(*) >= 50 "
            "ORDER BY late_rate DESC LIMIT 10;"
        ),
    },
    {
        "id": "H05",
        "level": "hard",
        # 808 审查 H3 换题（原题与 few_shot#10 重叠）：配送时长分桶与评分关系。
        # 首跑失败后修订：题面明确"整数天"口径与"一单一计"约定；
        # gold 修正为按订单去重计数（原 gold 的 COUNT(*) 实为评价行数）
        "question": (
            "配送时长与评分的关系：按配送天数（整数天）分桶（0-7 天 / 8-15 天 / 16-30 天 / 30 天以上）"
            "统计每桶的订单数（同一订单多条评价按一单计）和平均评分（保留 4 位小数）"
        ),
        "gold_sql": (
            "WITH delivery AS ("
            "  SELECT o.order_id, "
            "         CAST(julianday(o.order_delivered_customer_date) "
            "              - julianday(o.order_purchase_timestamp) AS INTEGER) AS days "
            "  FROM orders o "
            "  WHERE o.order_status = 'delivered' "
            "    AND o.order_delivered_customer_date IS NOT NULL"
            "), "
            "bucketed AS ("
            "  SELECT order_id, days, "
            "         CASE WHEN days <= 7 THEN '0-7天' "
            "              WHEN days <= 15 THEN '8-15天' "
            "              WHEN days <= 30 THEN '16-30天' "
            "              ELSE '>30天' END AS bucket "
            "  FROM delivery"
            "), "
            "order_avg AS ("
            "  SELECT order_id, AVG(review_score) AS avg_score "
            "  FROM order_reviews GROUP BY order_id"
            ") "
            "SELECT b.bucket, COUNT(*) AS order_cnt, "
            "ROUND(AVG(oa.avg_score), 4) AS avg_score "
            "FROM bucketed b LEFT JOIN order_avg oa ON oa.order_id = b.order_id "
            "GROUP BY b.bucket ORDER BY MIN(b.days);"
        ),
    },
    {
        "id": "H06",
        "level": "hard",
        # 按 customer_unique_id 聚合消费，再 re-join customers 按 customer_state 统计
        # （同一 unique_id 可能在多个 customer_state 出现，各州均计入）
        "question": "高价值客户（历史总消费 price 之和 > 500 BRL）的州分布（按客户数降序）",
        "gold_sql": (
            "WITH customer_spend AS ("
            "  SELECT c.customer_unique_id, SUM(oi.price) AS total_spend "
            "  FROM customers c "
            "  JOIN orders o ON o.customer_id = c.customer_id "
            "  JOIN order_items oi ON oi.order_id = o.order_id "
            "  GROUP BY c.customer_unique_id "
            "  HAVING SUM(oi.price) > 500"
            ") "
            "SELECT c.customer_state, COUNT(DISTINCT c.customer_unique_id) AS high_value_customers "
            "FROM customer_spend cs "
            "JOIN customers c ON c.customer_unique_id = cs.customer_unique_id "
            "GROUP BY c.customer_state ORDER BY high_value_customers DESC;"
        ),
    },
    {
        "id": "H07",
        "level": "hard",
        "question": "品类销量排名（用英文品类名，输出 category / item_cnt / rank，按 rank 升序取前 20）",
        "gold_sql": (
            "SELECT ct.product_category_name_english AS category, "
            "COUNT(*) AS item_cnt, "
            "RANK() OVER (ORDER BY COUNT(*) DESC) AS rnk "
            "FROM order_items oi "
            "JOIN products p ON p.product_id = oi.product_id "
            "JOIN category_translation ct ON ct.product_category_name = p.product_category_name "
            "GROUP BY category ORDER BY rnk LIMIT 20;"
        ),
    },
    {
        "id": "H08",
        "level": "hard",
        "question": "每个客户（customer_unique_id）的最近一次购买时间和历史总消费（price 之和，保留 2 位小数），按总消费降序 top 20",
        "gold_sql": (
            "SELECT c.customer_unique_id, "
            "MAX(o.order_purchase_timestamp) AS last_purchase, "
            "ROUND(SUM(oi.price), 2) AS total_spend "
            "FROM customers c "
            "JOIN orders o ON o.customer_id = c.customer_id "
            "JOIN order_items oi ON oi.order_id = o.order_id "
            "GROUP BY c.customer_unique_id "
            "ORDER BY total_spend DESC LIMIT 20;"
        ),
    },
    {
        "id": "H09",
        "level": "hard",
        "question": "有过取消或不可用（canceled / unavailable）订单记录的独立客户数",
        "gold_sql": (
            "SELECT COUNT(DISTINCT c.customer_unique_id) AS cnt "
            "FROM customers c JOIN orders o ON o.customer_id = c.customer_id "
            "WHERE o.order_status IN ('canceled', 'unavailable');"
        ),
    },
    {
        "id": "H10",
        "level": "hard",
        # 808 复审：题面显式指定输出列（与 H07 风格一致）——此前 gold 含
        # payment_type 常量列（WHERE 已限定 credit_card），模型两可输出导致形状抖动
        "question": (
            "各支付方式的分期付款分布：只取 credit_card，统计分期数（installments）"
            "各有多少笔支付记录，输出两列 installments、cnt，按分期数升序"
        ),
        "gold_sql": (
            "SELECT payment_installments AS installments, COUNT(*) AS cnt "
            "FROM order_payments "
            "WHERE payment_type = 'credit_card' "
            "GROUP BY payment_installments ORDER BY installments;"
        ),
    },
]


# ═══════════════════════════════════════════════════════════════
# 评测引擎
# ═══════════════════════════════════════════════════════════════

@dataclass
class EvalResult:
    case_id: str
    level: str
    question: str
    gold_sql: str
    pred_sql: str | None
    passed: bool
    error: str | None
    elapsed_ms: int


def _run_gold(sql: str) -> pd.DataFrame:
    engine = create_engine(f"sqlite:///{DB_PATH}")
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)


def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    """值级规范化：列名统一替换为位置编号，行排序，数值精度 4 位。

    列名不参与比较——模型生成语义等价但别名不同的 SQL（如 cnt vs
    order_cnt）不应被判 FAIL。只要列数相同、每列的值集合一致即通过。
    """
    df = df.copy()
    # 数值列四舍五入到 4 位，消除浮点差异
    for col in df.select_dtypes(include="number").columns:
        df[col] = df[col].round(4)
    # 按列的值排序（先按位置对列排序，再按行内容排序）
    # 用位置号替换列名，使 assert_frame_equal 不比较列名
    df.columns = [str(i) for i in range(len(df.columns))]
    df = df.sort_values(by=list(df.columns)).reset_index(drop=True)
    return df


def _dfs_equal(df1: pd.DataFrame, df2: pd.DataFrame) -> bool:
    """判断两个 DataFrame 结果是否等价。

    评测标准（宽松值对齐）：
    - 行数、列数必须相同
    - 忽略列名差异（只比较值）
    - 忽略行顺序
    - 数值容差 1e-3
    - 忽略列顺序：按各列值的排序字符串对列重新排列后再比较
    """
    if df1.shape != df2.shape:
        return False

    # 将每列值序列化为可比较的字符串指纹，用于对齐列顺序
    def _col_fingerprint(df: pd.DataFrame) -> list[str]:
        out = []
        for col in df.columns:
            s = df[col].copy()
            if pd.api.types.is_numeric_dtype(s):
                # round(3) 而非 round(4)：让指纹容纳 1e-3 级别的差异，
                # 与 assert_frame_equal 的 atol=1e-3 保持一致
                s = s.round(3)
            out.append("|".join(s.astype(str).sort_values().values))
        return out

    fp1 = _col_fingerprint(df1)
    fp2 = _col_fingerprint(df2)
    # 对两边按指纹排序，尝试对齐列顺序
    order1 = sorted(range(len(fp1)), key=lambda i: fp1[i])
    order2 = sorted(range(len(fp2)), key=lambda i: fp2[i])
    if sorted(fp1) != sorted(fp2):
        return False

    df1_aligned = df1.iloc[:, order1].copy()
    df2_aligned = df2.iloc[:, order2].copy()

    n1 = _normalize_df(df1_aligned)
    n2 = _normalize_df(df2_aligned)
    try:
        pd.testing.assert_frame_equal(
            n1, n2,
            check_dtype=False,
            check_names=False,
            check_exact=False,
            rtol=1e-3,
            atol=1e-3,
        )
        return True
    except AssertionError:
        return False


def run_eval(
    cases: list[dict],
    verbose: bool = False,
    level_filter: str | None = None,
) -> list[EvalResult]:
    if level_filter:
        cases = [c for c in cases if c["level"] == level_filter]

    results: list[EvalResult] = []
    total = len(cases)

    print(f"\n{'='*60}")
    print(f"  Text2SQL 基线评测  |  共 {total} 题  |  DB: olist.db")
    print(f"{'='*60}\n")

    for i, case in enumerate(cases, 1):
        cid = case["id"]
        q = case["question"]
        gold_sql = case["gold_sql"]
        t0 = time.time()

        print(f"[{i:02d}/{total}] {cid} ({case['level']})  {q[:40]}...")

        # 1. 执行 gold SQL，获取标准答案
        try:
            gold_df = _run_gold(gold_sql)
        except Exception as e:
            print(f"  ⚠  gold SQL 执行失败: {e}")
            results.append(EvalResult(
                case_id=cid, level=case["level"], question=q,
                gold_sql=gold_sql, pred_sql=None, passed=False,
                error=f"gold_sql_error: {e}",
                elapsed_ms=int((time.time() - t0) * 1000),
            ))
            continue

        # 2. 调用 Text2SQL pipeline（真实 LLM）
        try:
            qr = query_data(q)
            pred_sql = qr.sql
            pred_df = qr.df
            elapsed_ms = int((time.time() - t0) * 1000)
        except Exception as e:
            print(f"  ✗  pipeline 失败: {e}")
            results.append(EvalResult(
                case_id=cid, level=case["level"], question=q,
                gold_sql=gold_sql, pred_sql=None, passed=False,
                error=str(e),
                elapsed_ms=int((time.time() - t0) * 1000),
            ))
            continue

        # 3. 对比结果
        passed = _dfs_equal(gold_df, pred_df)
        status = "PASS" if passed else "FAIL"
        print(f"  {status}  attempts={qr.attempts}  rows={len(pred_df)}  elapsed={elapsed_ms}ms")

        if verbose or not passed:
            print(f"      gold rows={len(gold_df)}  pred rows={len(pred_df)}")
            print(f"      PRED SQL: {pred_sql}")
            if not passed:
                print(f"      GOLD SQL: {gold_sql}")
                print(f"      gold head:\n{gold_df.head(3).to_string(index=False)}")
                print(f"      pred head:\n{pred_df.head(3).to_string(index=False)}")

        results.append(EvalResult(
            case_id=cid, level=case["level"], question=q,
            gold_sql=gold_sql, pred_sql=pred_sql, passed=passed,
            error=None,
            elapsed_ms=elapsed_ms,
        ))

    return results


def print_summary(results: list[EvalResult]) -> None:
    print(f"\n{'='*60}")
    print("  评测结果汇总")
    print(f"{'='*60}")

    levels = ["easy", "medium", "hard"]
    grand_pass = 0
    grand_total = 0

    for lv in levels:
        sub = [r for r in results if r.level == lv]
        if not sub:
            continue
        passed = sum(1 for r in sub if r.passed)
        total = len(sub)
        acc = passed / total if total else 0
        grand_pass += passed
        grand_total += total
        bar = "#" * int(acc * 20) + "-" * (20 - int(acc * 20))
        print(f"  {lv.upper():7s}  [{bar}]  {passed:2d}/{total}  ({acc:.0%})")

    if grand_total:
        overall = grand_pass / grand_total
        bar = "#" * int(overall * 20) + "-" * (20 - int(overall * 20))
        print(f"  {'TOTAL':7s}  [{bar}]  {grand_pass:2d}/{grand_total}  ({overall:.0%})")

    # 失败题目清单
    failed = [r for r in results if not r.passed]
    if failed:
        print(f"\n  失败题目（{len(failed)} 题）：")
        for r in failed:
            err = f"  err={r.error[:60]}" if r.error else ""
            print(f"    {r.case_id}  {r.level:6s}  {r.question[:45]}{err}")

    print(f"{'='*60}\n")


# ═══════════════════════════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="Text2SQL 基线准确率评测")
    parser.add_argument("--verbose", "-v", action="store_true", help="输出每题详细 SQL 对比")
    parser.add_argument(
        "--level", choices=["easy", "medium", "hard"],
        help="只跑指定难度（不填则跑全部 50 题）",
    )
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"[ERROR] 找不到数据库: {DB_PATH}")
        print("  请先运行: python -m chatbi.load_olist")
        sys.exit(1)

    results = run_eval(EVAL_CASES, verbose=args.verbose, level_filter=args.level)
    print_summary(results)


if __name__ == "__main__":
    main()
