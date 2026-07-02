"""Tool misuse: swap one tool-call argument, then re-run the real mock backend against the
mutated input so tool_result stays internally consistent — only the downstream narrative
(final_summary, unchanged) is now wrong relative to what actually happened."""

from __future__ import annotations

import random
import uuid
from dataclasses import replace
from typing import Any

from ..models.mutation import Severity
from ..models.trajectory import ToolCall, ToolResult, Trajectory, with_step_replaced
from ..tasks.registry import Dispatch
from .shared import numeric_keys, perturb_numeric, state_before_step, steps_with_tool_calls


def apply(
    trajectory: Trajectory,
    severity: Severity,
    rng: random.Random,
    dispatch: Dispatch,
    initial_state: dict[str, Any],
) -> tuple[Trajectory, str, int]:
    candidates = steps_with_tool_calls(trajectory.steps)
    target = rng.choice(candidates)
    assert target.tool_call is not None

    tool_input = dict(target.tool_call.tool_input)
    keys = numeric_keys(tool_input) or [k for k, v in tool_input.items() if isinstance(v, str)]
    key = rng.choice(keys)
    original_value = tool_input[key]

    if isinstance(original_value, (int, float)):
        new_value: Any = perturb_numeric(float(original_value), severity, rng)
    elif severity == Severity.BLATANT:
        new_value = f"{original_value}-WRONG"
    else:
        new_value = f"{original_value} "  # subtle: trailing space, plausible typo-level change

    mutated_input = {**tool_input, key: new_value}
    state = state_before_step(trajectory.steps, dispatch, initial_state, target.step_index)
    new_result = dispatch(state, target.tool_call.tool_name, mutated_input)
    is_error = isinstance(new_result, dict) and "error" in new_result

    new_steps = with_step_replaced(
        trajectory.steps,
        target.step_index,
        tool_call=ToolCall(
            tool_name=target.tool_call.tool_name,
            tool_input=mutated_input,
            tool_use_id=target.tool_call.tool_use_id,
        ),
        tool_result=ToolResult(
            tool_use_id=target.tool_call.tool_use_id, content=new_result, is_error=is_error
        ),
    )

    mutated = replace(
        trajectory,
        trajectory_id=f"traj-{uuid.uuid4().hex[:12]}",
        steps=new_steps,
        ground_truth_correct=False,
    )
    description = (
        f"tool_misuse ({severity.value}): changed '{key}' from {original_value!r} to "
        f"{new_value!r} on step {target.step_index}'s {target.tool_call.tool_name} call"
    )
    return mutated, description, target.step_index
