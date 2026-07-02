"""Omission: delete a policy-required step from the trajectory entirely and re-index the
rest. final_summary is left exactly as originally written — the omission itself, with no
affirmative false claim, is what distinguishes this from instruction_violation."""

from __future__ import annotations

import random
import uuid
from dataclasses import replace
from typing import Any

from ..models.mutation import Severity
from ..models.trajectory import Trajectory, without_step
from ..tasks.registry import Dispatch

# Tool names whose presence represents "the policy-required step" across domains.
POLICY_TOOL_NAMES = {"request_supervisor_override", "request_budget_exception"}


def apply(
    trajectory: Trajectory,
    severity: Severity,
    rng: random.Random,
    dispatch: Dispatch,
    initial_state: dict[str, Any],
) -> tuple[Trajectory, str, int]:
    candidates = [
        s for s in trajectory.steps if s.tool_call and s.tool_call.tool_name in POLICY_TOOL_NAMES
    ]
    if not candidates:
        raise ValueError(
            "omission: trajectory has no policy-required step (an override/exception call) "
            "to remove"
        )
    target = rng.choice(candidates)
    assert target.tool_call is not None
    new_steps = without_step(trajectory.steps, target.step_index)

    mutated = replace(
        trajectory,
        trajectory_id=f"traj-{uuid.uuid4().hex[:12]}",
        steps=new_steps,
        ground_truth_correct=False,
    )
    description = (
        f"omission ({severity.value}): removed the policy-required "
        f"{target.tool_call.tool_name} call that was at step {target.step_index}"
    )
    return mutated, description, target.step_index
