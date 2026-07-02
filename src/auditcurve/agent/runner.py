"""Runs the untrusted strong agent against a Task via the Anthropic API, producing a
Trajectory. `ground_truth_correct` is left False here — the orchestration layer calls the
task's evaluator on the returned trajectory and fills it in, since the evaluator needs the
final Trajectory object to already exist."""

from __future__ import annotations

import copy
import json
import uuid
from typing import Any

from ..cost.calculator import timed_create
from ..cost.pricing import PricingTable
from ..models.cost import combine
from ..models.task import Task
from ..models.trajectory import ToolCall, ToolResult, Trajectory, TrajectoryStep
from .tool_dispatch import get_dispatch_for_domain

MAX_TURNS = 10
MAX_TOKENS_PER_CALL = 2048


def run_agent(
    client: Any,
    task: Task,
    model: str,
    pricing_table: PricingTable,
    trajectory_id: str | None = None,
) -> Trajectory:
    dispatch = get_dispatch_for_domain(task.domain)
    state = copy.deepcopy(task.initial_state)
    tools = task.anthropic_tools()

    messages: list[dict[str, Any]] = [{"role": "user", "content": task.user_request}]
    cost_records = []
    steps: list[TrajectoryStep] = []
    final_summary = ""
    step_index = 0

    for _ in range(MAX_TURNS):
        response, cost_record = timed_create(
            client,
            pricing_table,
            model=model,
            max_tokens=MAX_TOKENS_PER_CALL,
            system=task.system_prompt,
            thinking={"type": "disabled"},
            output_config={"effort": "low"},
            tools=tools,
            messages=messages,
        )
        cost_records.append(cost_record)

        text_parts = [b.text for b in response.content if b.type == "text"]
        reasoning_text = "\n".join(t for t in text_parts if t) or None
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

        messages.append({"role": "assistant", "content": response.content})

        if not tool_use_blocks:
            final_summary = reasoning_text or ""
            break

        tool_results_content: list[dict[str, Any]] = []
        for i, block in enumerate(tool_use_blocks):
            tool_input = dict(block.input)
            result = dispatch(state, block.name, tool_input)
            is_error = isinstance(result, dict) and "error" in result

            steps.append(
                TrajectoryStep(
                    step_index=step_index,
                    reasoning_text=reasoning_text if i == 0 else None,
                    tool_call=ToolCall(
                        tool_name=block.name, tool_input=tool_input, tool_use_id=block.id
                    ),
                    tool_result=ToolResult(tool_use_id=block.id, content=result, is_error=is_error),
                )
            )
            step_index += 1
            tool_results_content.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                    "is_error": is_error,
                }
            )

        messages.append({"role": "user", "content": tool_results_content})

        if response.stop_reason != "tool_use":
            break
    else:
        final_summary = (
            final_summary or "(agent did not produce a final summary within the turn limit)"
        )

    return Trajectory(
        trajectory_id=trajectory_id or f"traj-{uuid.uuid4().hex[:12]}",
        task_id=task.task_id,
        steps=steps,
        final_summary=final_summary,
        ground_truth_correct=False,
        cost_record=combine(cost_records),
    )
