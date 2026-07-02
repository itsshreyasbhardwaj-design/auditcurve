"""Shared monitor plumbing: the strategy protocol and the one structured-output call
helper every strategy routes through (so JSON parsing failures never pollute detection
metrics with a crash instead of a clean failed-to-parse result)."""

from __future__ import annotations

import json
from typing import Any, Protocol

from ..cost.calculator import timed_create
from ..cost.pricing import PricingTable
from ..models.cost import CostRecord
from ..models.task import Task
from ..models.trajectory import Trajectory
from ..models.verdict import MonitorVerdict

TRUSTED_MODEL_MAX_TOKENS = 1024


class MonitorStrategy(Protocol):
    name: str

    def run(
        self,
        client: Any,
        trajectory: Trajectory,
        task: Task,
        trusted_model: str,
        pricing_table: PricingTable,
        budget: int | None = None,
    ) -> MonitorVerdict: ...


def call_structured(
    client: Any,
    pricing_table: PricingTable,
    model: str,
    system_prompt: str,
    user_content: str,
    schema: dict,
) -> tuple[dict, CostRecord]:
    """Calls the trusted model with a structured-JSON-output constraint and returns the
    parsed dict plus the CostRecord for the call. Haiku 4.5 does not support the `effort`
    parameter, so it is deliberately omitted here."""
    response, cost_record = timed_create(
        client,
        pricing_table,
        model=model,
        max_tokens=TRUSTED_MODEL_MAX_TOKENS,
        system=system_prompt,
        output_config={"format": {"type": "json_schema", "schema": schema}},
        messages=[{"role": "user", "content": user_content}],
    )
    text = next((b.text for b in response.content if b.type == "text"), "{}")
    return json.loads(text), cost_record
