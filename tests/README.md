# tests/ — 测试

三层测试体系：

| 层 | 文件 | 依赖 | 何时跑 |
| --- | --- | --- | --- |
| 冒烟 | `smoke_agent.py` `smoke_introduce_me.py` `smoke_text2sql.py` `smoke_viz_explain.py` | 真实 LLM API + 向量库 + olist.db | 改了 prompt / 工具逻辑后 |
| 单元 | `test_*.py`（8 个） | 无外部依赖（mock LLM） | 每次改代码 |
| 评测 | `eval_text2sql.py` | 真实 LLM API + olist.db | Text2SQL prompt 迭代时对比基线 |

## 运行

```bash
# 冒烟（模块方式运行）
python -m tests.smoke_agent          # Agent 全链路（3 类问题）
python -m tests.smoke_introduce_me   # RAG 检索工具
python -m tests.smoke_text2sql       # Text2SQL 工具
python -m tests.smoke_viz_explain    # 可视化 + 解读工具

# 单元测试
pytest tests/ -v                     # 全部
pytest tests/test_text2sql.py -v     # Text2SQL pipeline（mock LLM：校验/重试/异常路径）
pytest tests/test_planner.py -v      # Planner JSON 提取与决策
pytest tests/test_graph.py -v        # 状态机 / 路由 / 工具分发
pytest tests/test_validator.py -v    # SQL 安全校验
pytest tests/test_visualize.py -v    # 自动选图规则
pytest tests/test_rag.py -v          # RAG 检索质量
pytest tests/test_rate_limit.py -v   # 限流
pytest tests/test_sanitize_input.py -v  # 注入清洗
pytest tests/test_public_chat.py -v  # 公开访问 /api/chat + 健康检查

# Text2SQL 基线评测（50 题：简单 20 + 中等 20 + 复杂 10，执行准确率判定）
python -m tests.eval_text2sql                  # 全部
python -m tests.eval_text2sql --level easy     # 按难度
python -m tests.eval_text2sql --verbose        # 打印每题详情
```

## 说明

- [conftest.py](conftest.py)：session 级自动 fixture——设 `SKIP_CONFIG_VALIDATION=1`（防止配置校验在测试中 `sys.exit`）和 HF 离线环境变量。
- `_check_db.py`：临时辅助脚本，检查 olist.db 各表行数、验证评测 gold SQL，非测试用例。
- 评测判定方式：gold SQL 与模型 SQL 分别查真实数据库，比较结果集等价（忽略行列顺序），不要求 SQL 字面一致。
