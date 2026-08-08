# chatbi/ — Text2SQL 数据模块

ChatBI 能力的数据底座：Olist 巴西电商数据集的 schema 描述、few-shot 示例、SQL 安全校验器，以及 CSV → SQLite 的导入脚本。被 [agent/tools/query_data.py](../agent/tools/query_data.py) 使用。

## 模块

| 文件 | 职责 |
| --- | --- |
| [schema.py](schema.py) | 9 张表的完整 schema 描述（字段 + 中文注释 + 表关系），注入 Text2SQL prompt |
| [few_shots.py](few_shots.py) | 10 组（问题, SQL）few-shot 示例，`format_few_shots()` 格式化注入 prompt |
| [validator.py](validator.py) | SQL 安全校验：只允许只读查询，详见下文 |
| [load_olist.py](load_olist.py) | CSV → SQLite 导入脚本（生成 `data/olist.db`） |
| `data/olist.db` | SQLite 数据库（9 表关联，orders 表 99441 行） |

## 数据集（Kaggle Olist 巴西电商）

```
customers ──< orders ──< order_items >── products ── category_translation（葡→英）
                  │            │
                  │            └── >── sellers
                  ├──< order_payments
                  └──< order_reviews
geolocation（独立，按邮编前缀关联）
```

9 张表：`customers` · `orders` · `order_items` · `order_payments` · `order_reviews` · `products` · `sellers` · `category_translation` · `geolocation`。

注意点（已写进 schema 注释和 prompt）：

- `customer_id` 不是自然人唯一标识，统计客户数用 `customer_unique_id` 去重。
- 时间字段是 TEXT（如 `order_purchase_timestamp`），用 `strftime` / `LIKE '2018%'` 过滤，不能用 `YEAR()`。
- 品类名是葡萄牙语，需 JOIN `category_translation` 转英文。

## SQL 安全校验（validator.py）

LLM 生成的 SQL 必须通过 `validate()` 才能执行：

- 只允许**单条语句**（sqlparse 解析后恰好 1 条）。
- 只允许 `SELECT` 或 `WITH ... SELECT`（CTE 会被 sqlparse 报为 UNKNOWN，单独识别放行；**`WITH RECURSIVE` 一律拒绝**——无终止递归可耗尽单机资源）。
- 关键字黑名单（16 个）：`INSERT` `UPDATE` `DELETE` `DROP` `ALTER` `CREATE` `TRUNCATE` `REPLACE` `ATTACH` `DETACH` `PRAGMA` `VACUUM` `REINDEX` `GRANT` `REVOKE` `EXPLAIN`。
- 函数形式黑名单：`pragma_*`（词边界 `\bPRAGMA\b` 匹配不到 `pragma_table_info` 这类表值函数）、`load_extension` / `readfile` / `writefile`。
- 检查前先剥离 SQL 注释和字符串字面量，避免 `SELECT 'INSERT'` 这类误杀。
- `clean_sql()` 顺手剥离 LLM 爱加的 markdown 代码围栏。

执行层另有护栏（在 [agent/tools/query_data.py](../agent/tools/query_data.py)）：**只读连接**（`mode=ro`）、**语句超时**（SQLite progress handler，15s）、**结果集上限**（1 万行截断）。

## Few-shot 示例（10 组）

覆盖：时间过滤+聚合、分组统计、JOIN+排序 top-N、多表 JOIN+去重计数、条件聚合、`COUNT(*)` vs `COUNT(DISTINCT)` 语义、多年长表对比、宽表（vs 对比）等。在 [few_shots.py](few_shots.py) 中增改。

注意：评测集（[tests/eval_text2sql.py](../tests/eval_text2sql.py)）与 few-shot **零重叠**（808 审查 H3 换题后的无泄漏基线 96%）——新增示例时不得从评测题抄写。

## 重建数据库

```bash
python -m chatbi.load_olist --src "data/olist数据集" --db chatbi/data/olist.db
```

CSV 文件名 → 表名的映射在 `load_olist.py` 的 `TABLE_MAP`。

## 测试

```bash
python -m tests.smoke_text2sql     # 工具冒烟（需真实 API Key）
pytest tests/test_validator.py -v  # 校验器单测
pytest tests/test_text2sql.py -v   # pipeline 单测（mock LLM）
python -m tests.eval_text2sql      # 50 题基线准确率评测（需真实 API Key + olist.db）
```
