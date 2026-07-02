"""Shared helpers used by every per-error-type mutation module (kept separate from
engine.py to avoid a circular import)."""

from __future__ import annotations

import copy
import random
from typing import Any

from ..models.mutation import Severity
from ..models.trajectory import TrajectoryStep
from ..tasks.registry import Dispatch


def perturb_numeric(value: float, severity: Severity, rng: random.Random) -> float:
    """Blatant = 20-40% deviation; subtle = 3-8% deviation. The one place severity has a
    consistent quantitative meaning across mutation types."""
    pct = rng.uniform(0.20, 0.40) if severity == Severity.BLATANT else rng.uniform(0.03, 0.08)
    sign = rng.choice([-1, 1])
    return round(value * (1 + sign * pct), 2)


def steps_with_tool_calls(steps: list[TrajectoryStep]) -> list[TrajectoryStep]:
    return [s for s in steps if s.tool_call is not None]


def numeric_keys(tool_input: dict) -> list[str]:
    return [
        k for k, v in tool_input.items() if isinstance(v, (int, float)) and not isinstance(v, bool)
    ]


def state_before_step(
    steps: list[TrajectoryStep],
    dispatch: Dispatch,
    initial_state: dict[str, Any],
    step_index: int,
) -> dict[str, Any]:
    """Replays every tool_call with step_index < `step_index` against a fresh copy of
    `initial_state`, giving the real backend state as of just before the target step —
    what a mutator needs to produce an internally-consistent tool_result for an edited call."""
    state = copy.deepcopy(initial_state)
    for step in steps:
        if step.tool_call is None or step.step_index >= step_index:
            continue
        dispatch(state, step.tool_call.tool_name, step.tool_call.tool_input)
    return state
