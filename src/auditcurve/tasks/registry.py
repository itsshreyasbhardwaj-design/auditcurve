"""Shared task registry + the replay-and-check helper every domain's evaluator reuses."""

from __future__ import annotations

import copy
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..models.task import Task
    from ..models.trajectory import Trajectory

Dispatch = Callable[[dict[str, Any], str, dict[str, Any]], Any]

_TASKS: dict[str, Task] = {}


def register_task(task: Task) -> None:
    if task.task_id in _TASKS:
        raise ValueError(f"Duplicate task_id: {task.task_id}")
    _TASKS[task.task_id] = task


def all_tasks() -> list[Task]:
    return list(_TASKS.values())


def get_task(task_id: str) -> Task:
    return _TASKS[task_id]


def replay_tool_calls(
    trajectory: Trajectory,
    dispatch: Dispatch,
    initial_state: dict[str, Any],
) -> tuple[dict[str, Any], list[tuple[str, dict[str, Any], Any]]]:
    """Replays every tool_call in `trajectory` against a *fresh* copy of `initial_state`
    using the domain's `dispatch` function, mutating a working state copy as it goes.
    Returns (final_state, [(tool_name, tool_input, result), ...]) in trajectory order.

    This is what makes evaluators trust the actual recorded tool_input arguments (which
    mutations edit) rather than whatever tool_result text happens to sit in the trajectory
    — the real backend re-runs, so a tampered tool_result is simply ignored/overridden.
    """
    state = copy.deepcopy(initial_state)
    results: list[tuple[str, dict[str, Any], Any]] = []
    for step in trajectory.steps:
        if step.tool_call is None:
            continue
        result = dispatch(state, step.tool_call.tool_name, step.tool_call.tool_input)
        results.append((step.tool_call.tool_name, step.tool_call.tool_input, result))
    return state, results


def _load_all_domains() -> None:
    """Imports every domain's tasks module so its register_task() calls run exactly once."""
    from .expenses import tasks as _expenses_tasks  # noqa: F401
    from .refunds import tasks as _refunds_tasks  # noqa: F401
    from .travel import tasks as _travel_tasks  # noqa: F401


_load_all_domains()
