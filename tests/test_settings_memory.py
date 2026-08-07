"""Memory/session 配置项解析测试（设计文档 §9）。"""

import importlib

import configs.settings as cfg


def test_memory_defaults_present():
    """7 个新配置项存在且默认值符合设计文档 §9。"""
    s = cfg.settings
    assert s.memory_recent_turns == 5
    assert s.memory_summary_trigger_turns == 10
    assert s.memory_summary_min_new_turns == 3
    assert s.memory_max_sessions_per_user == 50
    assert s.memory_max_age_days == 30
    assert s.memory_cleanup_interval_hours == 6
    assert s.summarizer_temperature == 0.3


def test_memory_env_override(monkeypatch):
    """环境变量覆盖生效（Settings 字段在类定义时读 env，需 reload 模块）。"""
    monkeypatch.setenv("MEMORY_RECENT_TURNS", "7")
    monkeypatch.setenv("SUMMARIZER_TEMPERATURE", "0.1")
    importlib.reload(cfg)
    try:
        assert cfg.settings.memory_recent_turns == 7
        assert cfg.settings.summarizer_temperature == 0.1
    finally:
        monkeypatch.undo()
        importlib.reload(cfg)
