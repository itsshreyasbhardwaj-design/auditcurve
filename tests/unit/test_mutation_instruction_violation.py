import random

import pytest

from auditcurve.models.mutation import ErrorType, Severity
from auditcurve.mutate.engine import apply_mutation


def test_instruction_violation_removes_policy_step_and_falsely_claims_compliance(
    refunds_task, refunds_correct_trajectory
):
    rng = random.Random(11)
    unit = apply_mutation(
        refunds_correct_trajectory,
        refunds_task,
        ErrorType.INSTRUCTION_VIOLATION,
        Severity.BLATANT,
        rng,
    )

    tool_names = [s.tool_call.tool_name for s in unit.trajectory.steps if s.tool_call]
    assert "request_supervisor_override" not in tool_names

    # unlike bare omission, the summary now affirmatively claims compliance
    assert unit.trajectory.final_summary != refunds_correct_trajectory.final_summary
    assert unit.trajectory.final_summary.startswith(refunds_correct_trajectory.final_summary)
    compliance_words = ("complies", "override", "procedure")
    assert any(w in unit.trajectory.final_summary.lower() for w in compliance_words)


def test_instruction_violation_raises_when_no_policy_step_present(
    refunds_task, refunds_violating_trajectory
):
    rng = random.Random(12)
    with pytest.raises(ValueError):
        apply_mutation(
            refunds_violating_trajectory,
            refunds_task,
            ErrorType.INSTRUCTION_VIOLATION,
            Severity.BLATANT,
            rng,
        )
