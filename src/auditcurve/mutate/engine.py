"""Mutation engine: "mutation testing" applied to agent trajectories. Given a correct
trajectory, produces exactly one labeled, controlled error. Ground truth (the Mutation
label) is produced alongside every mutated trajectory and is the *only* place labels
live — monitor code never receives a MutatedTrajectory, only the bare Trajectory inside it."""

from __future__ import annotations

import random
import uuid

from ..agent.tool_dispatch import get_dispatch_for_domain
from ..models.mutation import ErrorType, MutatedTrajectory, Mutation, Severity
from ..models.task import Task
from ..models.trajectory import Trajectory
from . import fabrication, instruction_violation, numeric_error, omission, tool_misuse

_MUTATORS = {
    ErrorType.TOOL_MISUSE: tool_misuse.apply,
    ErrorType.SILENT_NUMERIC_ERROR: numeric_error.apply,
    ErrorType.OMISSION: omission.apply,
    ErrorType.FABRICATION: fabrication.apply,
    ErrorType.INSTRUCTION_VIOLATION: instruction_violation.apply,
}


def applicable_error_types(trajectory: Trajectory) -> list[ErrorType]:
    """Which error types have at least one valid target in this trajectory. Omission and
    instruction_violation need a policy-required step (override/exception call) present;
    the others can always find a target given at least one tool call."""
    has_policy_step = any(
        s.tool_call and s.tool_call.tool_name in omission.POLICY_TOOL_NAMES
        for s in trajectory.steps
    )
    types = [ErrorType.TOOL_MISUSE, ErrorType.SILENT_NUMERIC_ERROR, ErrorType.FABRICATION]
    if has_policy_step:
        types += [ErrorType.OMISSION, ErrorType.INSTRUCTION_VIOLATION]
    return types


def apply_mutation(
    trajectory: Trajectory,
    task: Task,
    error_type: ErrorType,
    severity: Severity,
    rng: random.Random,
) -> MutatedTrajectory:
    dispatch = get_dispatch_for_domain(task.domain)
    mutator = _MUTATORS[error_type]
    new_trajectory, description, target_step_index = mutator(
        trajectory, severity, rng, dispatch, task.initial_state
    )

    mutation = Mutation(
        mutation_id=f"mut-{uuid.uuid4().hex[:12]}",
        error_type=error_type,
        severity=severity,
        target_step_index=target_step_index,
        description=description,
        original_trajectory_id=trajectory.trajectory_id,
    )
    return MutatedTrajectory(trajectory=new_trajectory, mutation=mutation, is_mutated=True)


def make_control(trajectory: Trajectory) -> MutatedTrajectory:
    """Wraps an untouched trajectory as the "unmutated control" unit of evaluation."""
    return MutatedTrajectory(trajectory=trajectory, mutation=None, is_mutated=False)
