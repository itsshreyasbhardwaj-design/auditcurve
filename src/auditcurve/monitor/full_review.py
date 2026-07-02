"""Full single-pass review: the monitor sees the entire trajectory in one call and renders
one verdict. The cheapest-per-call, most-informed-per-call strategy — the baseline the
other two are compared against."""

from __future__ import annotations

import uuid
from typing import Any

from ..cost.pricing import PricingTable
from ..models.task import Task
from ..models.trajectory import Trajectory
from ..models.verdict import MonitorVerdict
from .base import call_structured
from .prompts import NO_LOCALIZATION, SYSTEM_PROMPT, VERDICT_SCHEMA, render_full

NAME = "full_review"


def run(
    client: Any,
    trajectory: Trajectory,
    task: Task,
    trusted_model: str,
    pricing_table: PricingTable,
    budget: int | None = None,
) -> MonitorVerdict:
    policy_text = "; ".join(p.description for p in task.policy_constraints)
    user_content = render_full(trajectory, policy_text)

    parsed, cost_record = call_structured(
        client, pricing_table, trusted_model, SYSTEM_PROMPT, user_content, VERDICT_SCHEMA
    )

    localized = parsed.get("localized_step_index", NO_LOCALIZATION)
    return MonitorVerdict(
        verdict_id=f"verdict-{uuid.uuid4().hex[:12]}",
        strategy_name=NAME,
        trajectory_id=trajectory.trajectory_id,
        flagged=bool(parsed.get("flagged", False)),
        confidence=float(parsed.get("confidence", 0.0)),
        cost_record=cost_record,
        budget=None,
        localized_step_index=localized if localized != NO_LOCALIZATION else None,
        raw_response_text=str(parsed),
    )
