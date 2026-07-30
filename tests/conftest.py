"""Shared pytest fixtures and configuration for the Xiehaoyu-Agent test suite."""

from __future__ import annotations

import os
import pytest


# ── Session-level autouse fixtures ──────────────────────────


@pytest.fixture(scope="session", autouse=True)
def skip_config_validation():
    """Prevent configs/settings.py from calling sys.exit() during tests."""
    os.environ["SKIP_CONFIG_VALIDATION"] = "1"


@pytest.fixture(scope="session", autouse=True)
def set_offline_hf():
    """Prevent sentence-transformers from hitting HuggingFace Hub during tests."""
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")