"""Olist Brazilian e-commerce schema (SQLite). Used to build Text2SQL prompt.

关系速览：
    customers.customer_id           <-> orders.customer_id       (1-N: 一个客户可以有多笔订单)
    orders.order_id                 <-> order_items.order_id     (1-N)
    orders.order_id                 <-> order_payments.order_id  (1-N)
    orders.order_id                 <-> order_reviews.order_id   (1-N)
    order_items.product_id          <-> products.product_id
    order_items.seller_id           <-> sellers.seller_id
    products.product_category_name  <-> category_translation.product_category_name  (葡萄牙语 -> 英文)

注意：customer_id 是每笔订单分配的标识，不是自然人唯一标识。统计客户数时请使用 customer_unique_id。
"""

SCHEMA = """\
-- Olist 巴西电商数据集（SQLite）。所有时间字段是 TEXT，形如 '2018-01-05 12:34:56'。

TABLE customers (
    customer_id TEXT,               -- 一次下单会分配一个 customer_id
    customer_unique_id TEXT,        -- 同一自然人的稳定 id（跨订单）
    customer_zip_code_prefix BIGINT,
    customer_city TEXT,
    customer_state TEXT             -- 两位州代码，如 'SP'
);

TABLE orders (
    order_id TEXT,
    customer_id TEXT,               -- -> customers.customer_id
    order_status TEXT,              -- 'delivered' / 'shipped' / 'canceled' / ...
    order_purchase_timestamp TEXT,  -- 下单时间
    order_approved_at TEXT,
    order_delivered_carrier_date TEXT,
    order_delivered_customer_date TEXT,
    order_estimated_delivery_date TEXT
);

TABLE order_items (
    order_id TEXT,                  -- -> orders.order_id
    order_item_id BIGINT,           -- 同一订单内的商品序号
    product_id TEXT,                -- -> products.product_id
    seller_id TEXT,                 -- -> sellers.seller_id
    shipping_limit_date TEXT,
    price FLOAT,                    -- 单件价格（雷亚尔 BRL）
    freight_value FLOAT             -- 运费
);

TABLE order_payments (
    order_id TEXT,                  -- -> orders.order_id
    payment_sequential BIGINT,
    payment_type TEXT,              -- 'credit_card' / 'boleto' / 'voucher' / 'debit_card'
    payment_installments BIGINT,    -- 分期数
    payment_value FLOAT
);

TABLE order_reviews (
    review_id TEXT,
    order_id TEXT,                  -- -> orders.order_id
    review_score BIGINT,            -- 1~5
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TEXT,
    review_answer_timestamp TEXT
);

TABLE products (
    product_id TEXT,
    product_category_name TEXT,     -- 葡萄牙语；用 category_translation 转英文
    product_name_lenght FLOAT,
    product_description_lenght FLOAT,
    product_photos_qty FLOAT,
    product_weight_g FLOAT,
    product_length_cm FLOAT,
    product_height_cm FLOAT,
    product_width_cm FLOAT
);

TABLE sellers (
    seller_id TEXT,
    seller_zip_code_prefix BIGINT,
    seller_city TEXT,
    seller_state TEXT
);

TABLE category_translation (
    product_category_name TEXT,             -- 葡萄牙语
    product_category_name_english TEXT      -- 英文
);

TABLE geolocation (
    geolocation_zip_code_prefix BIGINT,
    geolocation_lat FLOAT,
    geolocation_lng FLOAT,
    geolocation_city TEXT,
    geolocation_state TEXT
);
"""
