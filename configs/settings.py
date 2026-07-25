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


@dataclass(frozen=True)
class Settings:
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    access_code: str = os.getenv("ACCESS_CODE", "")
    session_hourly_quota: int = int(os.getenv("SESSION_HOURLY_QUOTA", "50"))
    max_agent_steps: int = int(os.getenv("MAX_AGENT_STEPS", "5"))
    sql_retry_max: int = int(os.getenv("SQL_RETRY_MAX", "3"))
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-in-production-use-a-long-random-string-here")
    jwt_expire_hours: int = int(os.getenv("JWT_EXPIRE_HOURS", "24"))
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    # Temperature knobs (0.0 = deterministic, 0.3 = creative)
    planner_temperature: float = float(os.getenv("PLANNER_TEMPERATURE", "0.0"))
    text2sql_temperature: float = float(os.getenv("TEXT2SQL_TEMPERATURE", "0.0"))
    rag_temperature: float = float(os.getenv("RAG_TEMPERATURE", "0.3"))
    explain_temperature: float = float(os.getenv("EXPLAIN_TEMPERATURE", "0.3"))


def _validate() -> None:
    """Refuse to start with well-known insecure default secrets."""
    s = Settings()
    errors: list[str] = []

    if s.access_code == "":
        errors.append(
            "ACCESS_CODE is empty — set ACCESS_CODE in .env to a non-empty value."
        )
    if s.jwt_secret == "change-me-in-production-use-a-long-random-string-here":
        errors.append(
            "JWT_SECRET is still the default placeholder — "
            "generate a real secret with: python -c \"import secrets; print(secrets.token_hex(32))\""
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