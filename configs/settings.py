"""Central config: env vars, model names, rate-limit knobs."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    access_code: str = os.getenv("ACCESS_CODE", "")
    session_hourly_quota: int = 20
    max_agent_steps: int = 5
    sql_retry_max: int = 3


settings = Settings()
