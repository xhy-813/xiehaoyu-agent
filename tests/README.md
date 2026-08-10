# tests/ — 测试

三层测试体系：

| 层 | 文件 | 依赖 | 何时跑 |
| --- | --- | --- | --- |
| 冒烟 | `smoke_agent.py` `smoke_introduce_me.py` `smoke_text2sql.py` `smoke_viz_explain.py` `smoke_session_e2e.py` | 真实 LLM API + 向量库 + olist.db | 改了 prompt / 工具逻辑后 |
| 单元 | `test_*.py`（19 个） | 无外部依赖（mock LLM） | 每次改代码 |
| 评测 | `eval_text2sql.py` | 真实 LLM API + olist.db | Text2SQL prompt 迭代时对比基线 |

## 运行

```bash
# 冒烟（模块方式运行）
python -m tests.smoke_agent          # Agent 全链路（3 类问题）
python -m tests.smoke_introduce_me   # RAG 检索工具
python -m tests.smoke_text2sql       # Text2SQL 工具
python -m tests.smoke_viz_explain    # 可视化 + 解读工具
python -m tests.smoke_session_e2e    # 会话持久化端到端（新建→提问→追问→回放）

# 单元测试
pytest tests/ -v                        # 全部
pytest tests/test_text2sql.py -v        # Text2SQL pipeline（mock LLM：校验/重试/异常路径/执行护栏）
pytest tests/test_planner.py -v         # Planner JSON 提取与决策（含多行 JSON 回归用例）
pytest tests/test_graph.py -v           # 状态机 / 路由 / 工具分发（async 节点）
pytest tests/test_validator.py -v       # SQL 安全校验（含 RECURSIVE/函数黑名单）
pytest tests/test_visualize.py -v       # 自动选图规则
pytest tests/test_rag.py -v             # RAG 切片/检索/PII 脱敏
pytest tests/test_introduce_me.py -v    # RAG 工具（含检索降级诚实话术）
pytest tests/test_sanitize_input.py -v  # 注入清洗（中英文模式 + sanitize_history）
pytest tests/test_llm_client.py -v      # LLM 客户端工厂 + token 日志封装
pytest tests/test_rate_limit.py -v      # 限流（聊天桶 / 全局日上限 / 会话写桶 / IP 解析）
pytest tests/test_public_chat.py -v     # 公开访问 /api/chat + 健康检查 + ready 探活
pytest tests/test_user_dep.py -v        # X-User-Id 解析
pytest tests/test_session_store.py -v   # 会话 SQLite 存储 CRUD / 记忆上下文
pytest tests/test_sessions_api.py -v    # 会话 CRUD/搜索/回放 API
pytest tests/test_summarizer.py -v      # 摘要触发 / 标题生成
pytest tests/test_cleanup.py -v         # 过期/超量会话清理
pytest tests/test_memory_injection.py -v  # 记忆注入 planner
pytest tests/test_chat_persistence.py -v  # 聊天落库 + 匿名兼容
pytest tests/test_settings_memory.py -v   # 记忆配置项解析

# Text2SQL 基线评测（50 题：简单 20 + 中等 20 + 复杂 10，执行准确率判定）
python -m tests.eval_text2sql                  # 全部
python -m tests.eval_text2sql --level easy     # 按难度
python -m tests.eval_text2sql --verbose        # 打印每题详情
```

## 说明

- [conftest.py](conftest.py)：session 级自动 fixture——设 `SKIP_CONFIG_VALIDATION=1`（防止配置校验在测试中 `sys.exit`）和 HF 离线环境变量。
- `_check_db.py`：临时辅助脚本，检查 olist.db 各表行数、验证评测 gold SQL，非测试用例。
- 评测判定方式：gold SQL 与模型 SQL 分别查真实数据库，比较结果集等价（忽略行列顺序），不要求 SQL 字面一致。
- 评测集与 `chatbi/few_shots.py` **零重叠**（808 审查 H3 换题，无泄漏基线 96% = 48/50，EASY 100% / MEDIUM 95% / HARD 90%）——新增评测题时先比对 few-shot 避免泄漏。
