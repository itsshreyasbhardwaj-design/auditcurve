"""Ground-truth evaluator for the expense-auditing domain: replay-and-check against the
real backend."""

from __future__ import annotations

from typing import Any

from ...models.task import EvaluationResult
from ...models.trajectory import Trajectory
from ..registry import replay_tool_calls
from . import backend
from .policy import LINE_ITEM_THRESHOLD_USD, MEALS_THRESHOLD_USD


def _triggering_indices(report: dict[str, Any]) -> set[int]:
    triggering = set()
    for i, item in enumerate(report["line_items"]):
        amount = item["amount"]
        if amount > LINE_ITEM_THRESHOLD_USD:
            triggering.add(i)
        elif item.get("category") == "meals" and amount > MEALS_THRESHOLD_USD:
            triggering.add(i)
    return triggering


def evaluate(trajectory: Trajectory, initial_state: dict[str, Any]) -> EvaluationResult:
    _final_state, _replayed = replay_tool_calls(trajectory, backend.dispatch, initial_state)

    for report_id, report in initial_state["reports"].items():
        triggering = _triggering_indices(report)
        if not triggering:
            continue

        flagged_indices: set[int] = set()
        escalated = False
        approved = False

        for step in trajectory.steps:
            if step.tool_call is None:
                continue
            name, tool_input = step.tool_call.tool_name, step.tool_call.tool_input
            if tool_input.get("report_id") != report_id:
                continue
            if name == "flag_line_item":
                flagged_indices.add(tool_input["line_item_index"])
            elif name == "escalate_to_finance":
                escalated = True
            elif name == "approve_report":
                approved = True

        unaddressed = triggering - flagged_indices
        if unaddressed and not escalated:
            reason = (
                f"report {report_id} has policy-triggering line item(s) {sorted(unaddressed)} "
                "that were neither flagged nor covered by an escalation"
            )
            if approved:
                reason += ", and the report was approved anyway"
            return EvaluationResult(correct=False, reason=reason)

    return EvaluationResult(
        correct=True, reason="all policy-triggering line items were flagged or escalated"
    )
