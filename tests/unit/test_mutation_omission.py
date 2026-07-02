import random

import pytest

from auditcurve.models.mutation import ErrorType, Severity
from auditcurve.mutate.engine import apply_mutation


def test_omission_removes_the_policy_required_step(refunds_task, refunds_correct_trajectory):
    rng = random.Random(5)
    unit = apply_mutation(
        refunds_correct_trajectory, refunds_task, ErrorType.OMISSION, Severity.BLATANT, rng
    )

    tool_names = [s.tool_call.tool_name for s in unit.trajectory.steps if s.tool_call]
    assert "request_supervisor_override" not in tool_names
    assert len(unit.trajectory.steps) == len(refunds_correct_trajectory.steps) - 1


def test_omission_reindexes_contiguously(refunds_task, refunds_correct_trajectory):
    rng = random.Random(5)
    unit = apply_mutation(
        refunds_correct_trajectory, refunds_task, ErrorType.OMISSION, Severity.BLATANT, rng
    )
    assert [s.step_index for s in unit.trajectory.steps] == list(range(len(unit.trajectory.steps)))


def test_omission_leaves_final_summary_untouched(refunds_task, refunds_correct_trajectory):
    rng = random.Random(5)
    unit = apply_mutation(
        refunds_correct_trajectory, refunds_task, ErrorType.OMISSION, Severity.BLATANT, rng
    )
    assert unit.trajectory.final_summary == refunds_correct_trajectory.final_summary


def test_omission_raises_when_no_policy_step_present(refunds_task, refunds_violating_trajectory):
    rng = random.Random(6)
    with pytest.raises(ValueError):
        apply_mutation(
            refunds_violating_trajectory, refunds_task, ErrorType.OMISSION, Severity.BLATANT, rng
        )
