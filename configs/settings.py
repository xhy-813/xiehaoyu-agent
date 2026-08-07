"""Central config: env vars, model names, rate-limit knobs.

All values that can be configured via environment variables are read from
``os.getenv()`` so that editing ``.env`` actually takes effect.  The
constructor also validates that security-sensitive values have been
changed from their insecure defaults.
"""

import os
import sys
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _get_int(name: str, default: str) -> int:
    """Parse an integer env var with a clear error message on failure."""
    raw = os.getenv(name, default)
    try:
        return int(raw)
    except (ValueError, TypeError):
        print(
            f"[FATAL] {name}={raw!r} is not a valid integer — check your .env file.",
            file=sys.stderr,
        )
        sys.exit(1)


def _get_float(name: str, default: str) -> float:
    """Parse a float env var with a clear error message on failure."""
    raw = os.getenv(name, default)
    try:
        return float(raw)
    except (ValueError, TypeError):
        print(
            f"[FATAL] {name}={raw!r} is not a valid float — check your .env file.",
            file=sys.stderr,
        )
        sys.exit(1)


@dataclass(frozen=True)
class Settings:
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    ip_hourly_quota: int = _get_int("IP_HOURLY_QUOTA", "20")
    global_daily_quota: int = _get_int("GLOBAL_DAILY_QUOTA", "200")
    max_agent_steps: int = _get_int("MAX_AGENT_STEPS", "5")
    sql_retry_max: int = _get_int("SQL_RETRY_MAX", "3")
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    # Temperature knobs (0.0 = deterministic, 0.3 = creative)
    planner_temperature: float = _get_float("PLANNER_TEMPERATURE", "0.0")
    text2sql_temperature: float = _get_float("TEXT2SQL_TEMPERATURE", "0.0")
    rag_temperature: float = _get_float("RAG_TEMPERATURE", "0.3")
    explain_temperature: float = _get_float("EXPLAIN_TEMPERATURE", "0.3")

    # 对话记忆持久化（功能一，设计文档 §9；全部有安全默认值）
    memory_recent_turns: int = _get_int("MEMORY_RECENT_TURNS", "5")
    memory_summary_trigger_turns: int = _get_int("MEMORY_SUMMARY_TRIGGER_TURNS", "10")
    memory_summary_min_new_turns: int = _get_int("MEMORY_SUMMARY_MIN_NEW_TURNS", "3")
    memory_max_sessions_per_user: int = _get_int("MEMORY_MAX_SESSIONS_PER_USER", "50")
    memory_max_age_days: int = _get_int("MEMORY_MAX_AGE_DAYS", "30")
    memory_cleanup_interval_hours: int = _get_int("MEMORY_CLEANUP_INTERVAL_HOURS", "6")
    summarizer_temperature: float = _get_float("SUMMARIZER_TEMPERATURE", "0.3")


def _validate() -> None:
    """Refuse to start with well-known insecure default secrets."""
    s = Settings()
    errors: list[str] = []

    if not s.deepseek_api_key:
        errors.append(
            "DEEPSEEK_API_KEY is empty — set DEEPSEEK_API_KEY in .env to your DeepSeek API key."
        )

    if errors:
        for msg in errors:
            print(f"[FATAL] {msg}", file=sys.stderr)
        sys.exit(1)


settings = Settings()


# Run validation at import time so misconfigured deployments fail fast.
# Skip during test runs that set the env var.
if os.getenv("SKIP_CONFIG_VALIDATION", "").lower() not in ("1", "true", "yes"):
    _validate()