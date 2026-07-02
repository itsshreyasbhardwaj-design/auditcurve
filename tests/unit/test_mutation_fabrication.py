import random

from auditcurve.models.mutation import ErrorType, Severity
from auditcurve.models.trajectory import Trajectory
from auditcurve.mutate.engine import apply_mutation


def test_fabrication_substitutes_a_cited_id(refunds_task, refunds_correct_trajectory):
    rng = random.Random(7)
    unit = apply_mutation(
        refunds_correct_trajectory, refunds_task, ErrorType.FABRICATION, Severity.BLATANT, rng
    )

    assert unit.trajectory.final_summary != refunds_correct_trajectory.final_summary
    assert "id-substitution" in unit.mutation.description
    assert "-9999" in unit.trajectory.final_summary


def test_fabrication_subtle_id_substitution_replaces_exactly_one_cited_id(
    refunds_task, refunds_correct_trajectory
):
    rng = random.Random(9)
    unit = apply_mutation(
        refunds_correct_trajectory, refunds_task, ErrorType.FABRICATION, Severity.SUBTLE, rng
    )

    original_ids = {"OVR-0001", "REF-0001"}
    still_present = {i for i in original_ids if i in unit.trajectory.final_summary}
    assert len(still_present) == 1, "exactly one of the two original IDs should have been replaced"


def test_fabrication_falls_back_to_injected_claim_when_no_id_is_cited(refunds_task):
    traj = Trajectory(
        trajectory_id="t",
        task_id=refunds_task.task_id,
        steps=[],
        final_summary="All done, no issues.",
        ground_truth_correct=True,
    )
    rng = random.Random(8)
    unit = apply_mutation(traj, refunds_task, ErrorType.FABRICATION, Severity.SUBTLE, rng)

    assert unit.trajectory.final_summary.startswith("All done, no issues.")
    assert unit.trajectory.final_summary != traj.final_summary
    assert "injected-claim" in unit.mutation.description
