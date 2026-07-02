import random

from auditcurve.models.mutation import ErrorType, Severity
from auditcurve.mutate.engine import apply_mutation


def test_numeric_error_changes_the_trajectory(refunds_task, refunds_correct_trajectory):
    rng = random.Random(10)
    unit = apply_mutation(
        refunds_correct_trajectory,
        refunds_task,
        ErrorType.SILENT_NUMERIC_ERROR,
        Severity.BLATANT,
        rng,
    )
    assert unit.is_mutated
    assert unit.mutation.error_type == ErrorType.SILENT_NUMERIC_ERROR
    changed = (
        unit.trajectory.final_summary != refunds_correct_trajectory.final_summary
        or unit.trajectory.steps != refunds_correct_trajectory.steps
    )
    assert changed


def test_numeric_error_exercises_both_submodes_across_seeds(
    refunds_task, refunds_correct_trajectory
):
    seen_modes = set()
    for seed in range(30):
        rng = random.Random(seed)
        unit = apply_mutation(
            refunds_correct_trajectory,
            refunds_task,
            ErrorType.SILENT_NUMERIC_ERROR,
            Severity.SUBTLE,
            rng,
        )
        if "result-tampering" in unit.mutation.description:
            seen_modes.add("result")
        elif "citation-tampering" in unit.mutation.description:
            seen_modes.add("citation")
    assert seen_modes == {"result", "citation"}


def test_citation_tampering_target_step_index_points_past_the_last_step(
    refunds_task, refunds_correct_trajectory
):
    for seed in range(30):
        rng = random.Random(seed)
        unit = apply_mutation(
            refunds_correct_trajectory,
            refunds_task,
            ErrorType.SILENT_NUMERIC_ERROR,
            Severity.SUBTLE,
            rng,
        )
        if "citation-tampering" in unit.mutation.description:
            assert unit.mutation.target_step_index == len(refunds_correct_trajectory.steps)
            return
    raise AssertionError("citation-tampering mode never triggered across 30 seeds")
