from auditcurve.analysis.metrics import (
    ConfusionCounts,
    compute_confusion_counts,
    detection_latency,
    localization_accuracy,
    metrics_by_group,
    precision_recall_f1,
)
from auditcurve.models.cost import CostRecord
from auditcurve.models.mutation import ErrorType, MutatedTrajectory, Mutation, Severity
from auditcurve.models.trajectory import Trajectory
from auditcurve.models.verdict import MonitorVerdict


def _cost() -> CostRecord:
    return CostRecord(
        model="claude-haiku-4-5",
        input_tokens=1,
        output_tokens=1,
        cost_usd=0.001,
        latency_ms=1.0,
        timestamp="t",
    )


def _traj(tid: str) -> Trajectory:
    return Trajectory(
        trajectory_id=tid, task_id="t", steps=[], final_summary="", ground_truth_correct=True
    )


def _mutated(tid: str, target_step_index: int = 2) -> MutatedTrajectory:
    return MutatedTrajectory(
        trajectory=_traj(tid),
        mutation=Mutation(
            mutation_id=f"mut-{tid}",
            error_type=ErrorType.OMISSION,
            severity=Severity.BLATANT,
            target_step_index=target_step_index,
            description="d",
            original_trajectory_id=tid,
        ),
        is_mutated=True,
    )


def _control(tid: str) -> MutatedTrajectory:
    return MutatedTrajectory(trajectory=_traj(tid), mutation=None, is_mutated=False)


def _verdict(
    tid: str, flagged: bool, strategy="full_review", localized=None, flagged_at=None
) -> MonitorVerdict:
    return MonitorVerdict(
        verdict_id=f"v-{tid}",
        strategy_name=strategy,
        trajectory_id=tid,
        flagged=flagged,
        confidence=0.9,
        cost_record=_cost(),
        localized_step_index=localized,
        flagged_at_step_index=flagged_at,
    )


def test_precision_recall_f1_known_values():
    # 2 TP, 1 FP, 1 FN, 0 TN -> precision=2/3, recall=2/3, f1=2/3
    counts = ConfusionCounts(tp=2, fp=1, fn=1, tn=0)
    precision, recall, f1 = precision_recall_f1(counts)
    assert round(precision, 4) == round(2 / 3, 4)
    assert round(recall, 4) == round(2 / 3, 4)
    assert round(f1, 4) == round(2 / 3, 4)


def test_precision_recall_f1_all_zero_is_safe():
    assert precision_recall_f1(ConfusionCounts(0, 0, 0, 0)) == (0.0, 0.0, 0.0)


def test_compute_confusion_counts():
    mutations = [_mutated("m1"), _mutated("m2"), _control("c1"), _control("c2")]
    verdicts = [
        _verdict("m1", flagged=True),  # TP
        _verdict("m2", flagged=False),  # FN
        _verdict("c1", flagged=True),  # FP
        _verdict("c2", flagged=False),  # TN
    ]
    counts = compute_confusion_counts(verdicts, mutations)
    assert counts == ConfusionCounts(tp=1, fp=1, fn=1, tn=1)


def test_metrics_by_group_error_type():
    mutations = [_mutated("m1")]
    verdicts = [_verdict("m1", flagged=True)]
    grouped = metrics_by_group(verdicts, mutations, "error_type")
    assert "omission" in grouped
    assert grouped["omission"] == (1.0, 1.0, 1.0)


def test_localization_accuracy():
    mutations = [_mutated("m1", target_step_index=3), _mutated("m2", target_step_index=5)]
    verdicts = [
        _verdict("m1", flagged=True, localized=3),  # correct localization
        _verdict("m2", flagged=True, localized=1),  # wrong localization
    ]
    assert localization_accuracy(verdicts, mutations) == 0.5


def test_localization_accuracy_ignores_unflagged():
    mutations = [_mutated("m1", target_step_index=3)]
    verdicts = [_verdict("m1", flagged=False, localized=None)]
    assert localization_accuracy(verdicts, mutations) == 0.0


def test_detection_latency_only_counts_streaming_flags():
    mutations = [_mutated("m1", target_step_index=2)]
    verdicts = [
        _verdict("m1", flagged=True, strategy="streaming", flagged_at=2),
        _verdict("m1", flagged=True, strategy="full_review", flagged_at=None),
    ]
    latencies = detection_latency(verdicts, mutations)
    assert latencies == [0]
