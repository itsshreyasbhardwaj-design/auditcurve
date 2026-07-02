"""Gates every test in this directory behind a real ANTHROPIC_API_KEY — these tests spend
real (small) amounts of money and must never run in CI."""

from __future__ import annotations

import os

import pytest

requires_api_key = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set; skipping live API integration test",
)
