"""Shared pytest fixtures."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_pneuma_path() -> Path:
    return FIXTURES_DIR / "sample_pneuma.csv"


@pytest.fixture
def integration_dsn() -> str:
    """DSN for a live Postgres. Tests using this are skipped if it's not set."""
    dsn = os.environ.get("INTEGRATION_DSN")
    if not dsn:
        pytest.skip("INTEGRATION_DSN not set; skipping integration test")
    return dsn
