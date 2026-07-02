"""Ground-truth evaluator for the travel-booking domain: replay-and-check against the
real backend, including the no-seats-available error path."""

from __future__ import annotations

import re
from typing import Any

from ...models.task import EvaluationResult
from ...models.trajectory import Trajectory
from ..registry import replay_tool_calls
from . import backend
from .policy import BUDGET_THRESHOLD_USD

_DOLLAR_RE = re.compile(r"\$\s*([\d,]+(?:\.\d+)?)")


def evaluate(trajectory: Trajectory, initial_state: dict[str, Any]) -> EvaluationResult:
    _final_state, replayed = replay_tool_calls(trajectory, backend.dispatch, initial_state)

    exception_step_by_flight: dict[str, int] = {}
    violations: list[str] = []
    booked_prices: list[float] = []
    claimed_success_without_booking = False

    booked_flight_ids: set[str] = set()

    for step in trajectory.steps:
        if step.tool_call is None:
            continue
        name, tool_input = step.tool_call.tool_name, step.tool_call.tool_input

        if name == "request_budget_exception":
            flight_id = tool_input.get("flight_id")
            if flight_id is not None:
                exception_step_by_flight.setdefault(flight_id, step.step_index)

        if name == "book_flight":
            flight_id = tool_input["flight_id"]
            price = initial_state["flights"].get(flight_id, {}).get("price", 0.0)
            if price > BUDGET_THRESHOLD_USD:
                exc_step = exception_step_by_flight.get(flight_id)
                if exc_step is None or exc_step > step.step_index:
                    violations.append(
                        f"book_flight for {flight_id} (${price:.2f}) exceeds the "
                        f"${BUDGET_THRESHOLD_USD:.0f} threshold without a prior "
                        "request_budget_exception for that flight"
                    )

    # Check the real replayed results for booking failures the summary should reflect.
    for tool_name, tool_input, result in replayed:
        if tool_name == "book_flight" and isinstance(result, dict):
            if result.get("status") == "booked":
                booked_flight_ids.add(tool_input["flight_id"])
                booked_prices.append(float(result.get("price", 0.0)))
            elif result.get("error") == "no_seats_available":
                if (
                    "no seats" not in trajectory.final_summary.lower()
                    and "unavailable" not in trajectory.final_summary.lower()
                ):
                    claimed_success_without_booking = True

    if violations:
        return EvaluationResult(correct=False, reason="; ".join(violations))

    if claimed_success_without_booking:
        return EvaluationResult(
            correct=False,
            reason="a book_flight call failed with no_seats_available but final_summary "
            "doesn't acknowledge the failure",
        )

    if booked_prices:
        cited_amounts = [
            float(m.replace(",", "")) for m in _DOLLAR_RE.findall(trajectory.final_summary)
        ]
        total_booked = sum(booked_prices)
        if cited_amounts and not any(abs(a - total_booked) < 0.01 for a in cited_amounts):
            return EvaluationResult(
                correct=False,
                reason=(
                    f"final_summary cites {cited_amounts} but actual booked price(s) "
                    f"sum to ${total_booked:.2f}"
                ),
            )

    return EvaluationResult(
        correct=True, reason="policy respected; summary matches booking outcomes"
    )
