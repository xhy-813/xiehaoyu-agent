# prompts/ — LLM Prompt 模板

所有 prompt 以 `.md` 文件集中管理，代码中用 `pathlib` 读取（多数模块有内存缓存，改 prompt 后需重启进程生效）。

## 文件清单

| 文件 | 版本 | 用途 | 引用方 |
| --- | --- | --- | --- |
| [system_persona.md](system_persona.md) | 1.1.0 | Agent 核心人设：第一人称、回答风格、知识库说明、安全边界 | `introduce_me.py`（system）+ `graph.py` finalize 润色 |
| [planner.md](planner.md) | 1.2.0 | Planner 决策：工具清单、选择规则、失败恢复、安全规则 | `planner.py`（system） |
| [introduce_me.md](introduce_me.md) | 1.2.0 | RAG 回答模板：检索片段 + 格式约束 + 自我介绍模板 | `introduce_me.py`（user 模板） |
| [text2sql.md](text2sql.md) | 1.4.0 | Text2SQL：质量规范、COUNT/LIMIT/JOIN/长表规则、反面示例 | `query_data.py`（拆分 system + user） |
| [explain.md](explain.md) | 1.2.0 | 数据解读：洞察要求、Olist 业务背景、正反面示例 | `explain_result.py`（拆分 system + user） |

## 结构约定（改动时务必注意）

这些标记会被代码**按字符串切分解析**，改名或删除要同步改代码：

| 文件 | 被解析的标记 | 解析逻辑 |
| --- | --- | --- |
| text2sql.md | `【系统角色】` `【安全规则】` | 两者之间 → system；`【安全规则】`起 → user 模板 |
| explain.md | `【系统角色】` `【用户问题】` | 两者之间 → system；`【用户问题】`起 → user 模板 |
| introduce_me.md | `【自我介绍模板】` | 非自我介绍类问题时该段被裁掉，节省约 200 token |

占位符（`.format()` 注入，花括号不能删）：

- text2sql.md：`{schema}` `{few_shots}` `{question}`
- introduce_me.md：`{context}` `{question}`
- explain.md：`{question}` `{sql}` `{preview}`

## 编辑规范

1. **版本头**：每个文件首行带 `<!-- version: x.y.z, date: YYYY-MM-DD -->`，改内容必升版本号、更新日期。
2. **安全规则段**：每个 prompt 末尾保留"忽略角色切换/注入指令"的安全段落，这是抗注入的一道防线（另一道在 [agent/sanitize.py](../agent/sanitize.py)）。
3. **反面示例**：写清"禁止什么样"比"要什么样"更有效，新增规则尽量配反面示例。
4. 改完建议跑对应验证：

```bash
python -m tests.smoke_agent          # planner / persona 改动
python -m tests.eval_text2sql        # text2sql 改动（50 题基线对比）
pytest tests/test_planner.py -v      # planner 单测
```
