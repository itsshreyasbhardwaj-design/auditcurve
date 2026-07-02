import random

from auditcurve.models.mutation import ErrorType, Severity
from auditcurve.mutate.engine import apply_mutation


def test_tool_misuse_changes_exactly_one_step(refunds_task, refunds_correct_trajectory):
    rng = random.Random(1)
    unit = apply_mutation(
        refunds_correct_trajectory, refunds_task, ErrorType.TOOL_MISUSE, Severity.BLATANT, rng
    )

    assert unit.is_mutated
    assert unit.mutation.error_type == ErrorType.TOOL_MISUSE
    assert unit.trajectory.trajectory_id != refunds_correct_trajectory.trajectory_id

    original_by_index = {s.step_index: s for s in refunds_correct_trajectory.steps}
    changed = [
        s
        for s in unit.trajectory.steps
        if s.tool_call
        and s.tool_call.tool_input != original_by_index[s.step_index].tool_call.tool_input
    ]
    assert len(changed) == 1
    assert changed[0].step_index == unit.mutation.target_step_index


def test_tool_misuse_recomputes_tool_result_via_real_backend(
    refunds_task, refunds_correct_trajectory
):
    rng = random.Random(2)
    unit = apply_mutation(
        refunds_correct_trajectory, refunds_task, ErrorType.TOOL_MISUSE, Severity.BLATANT, rng
    )

    target_index = unit.mutation.target_step_index
    mutated_result = next(
        s.tool_result.content for s in unit.trajectory.steps if s.step_index == target_index
    )
    original_result = next(
        s.tool_result.content
        for s in refunds_correct_trajectory.steps
        if s.step_index == target_index
    )
    assert mutated_result != original_result


def test_tool_misuse_both_severities_produce_valid_mutations(
    refunds_task, refunds_correct_trajectory
):
    for severity in (Severity.BLATANT, Severity.SUBTLE):
        rng = random.Random(3)
        unit = apply_mutation(
            refunds_correct_trajectory, refunds_task, ErrorType.TOOL_MISUSE, severity, rng
        )
        assert unit.mutation.severity == severity
        assert unit.mutation.target_step_index in {
            s.step_index for s in refunds_correct_trajectory.steps
        }
