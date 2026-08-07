# SQL 执行顺序

## 问题分析
- 面试官意图：考察 SQL 基础功，是否理解查询引擎的执行逻辑
- 回答策略：按正确顺序列出，可以简单说明每一步的作用

## 关键信息
- 顺序：FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT

## 详细内容

SQL 执行顺序：

| 顺序 | 关键字 | 作用 |
|------|--------|------|
| 1 | FROM | 确定数据来源表 |
| 2 | WHERE | 过滤行数据 |
| 3 | GROUP BY | 分组聚合 |
| 4 | HAVING | 过滤分组结果 |
| 5 | SELECT | 选取字段 |
| 6 | ORDER BY | 排序 |
| 7 | LIMIT | 限制返回条数 |

## 面试话术

SQL 执行顺序是：先执行 FROM 确定表，然后 WHERE 过滤行，接着 GROUP BY 分组，再用 HAVING 过滤分组，然后 SELECT 取字段，最后 ORDER BY 排序和 LIMIT 限制条数。
