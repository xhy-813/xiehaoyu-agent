# configs/ — 全局配置

单一模块 [settings.py](settings.py)：从 `.env` 读取全部环境变量，导出冻结数据类实例 `settings` 供全项目使用。

## 机制

- 所有配置项经 `os.getenv()` 读取，改 `.env` 即生效；数字项用 `_get_int` / `_get_float` 解析，非法值直接报错退出。
- **启动校验**：模块 import 时检查 `DEEPSEEK_API_KEY` 非空，缺失则拒绝启动（fail fast）。测试场景设 `SKIP_CONFIG_VALIDATION=1` 跳过（见 [tests/conftest.py](../tests/conftest.py)）。

## 配置项

完整的环境变量表（默认值、说明）维护在根 [README.md 配置参考](../README.md#配置参考)，此处不重复。

## 使用

```python
from configs.settings import settings

settings.deepseek_model      # LLM 模型名
settings.max_agent_steps     # Agent 最大步数
settings.ip_hourly_quota     # 每 IP 每小时限流配额
```

新增配置项：在 `Settings` 数据类加字段（`os.getenv` 读入）→ 更新 `.env.example` → 更新根 README 配置表。
