from auditcurve.models.cost import CostRecord, combine
from auditcurve.models.mutation import ErrorType, MutatedTrajectory, Mutation, Severity
from auditcurve.models.trajectory import ToolCall, ToolResult, Trajectory, TrajectoryStep
from auditcurve.models.verdict import MonitorVerdict


def _cost(cost_usd: float = 0.01) -> CostRecord:
    return CostRecord(
        model="claude-haiku-4-5",
        input_tokens=100,
        output_tokens=20,
        cost_usd=cost_usd,
        latency_ms=100.0,
        timestamp="2026-06-24T00:00:00+00:00",
        cache_read_input_tokens=5,
        cache_creation_input_tokens=0,
    )


def test_cost_record_round_trip():
    record = _cost()
    assert CostRecord.from_dict(record.to_dict()) == record


def test_combine_sums_fields():
    a = _cost(0.01)
    b = _cost(0.02)
    combined = combine([a, b])
    assert combined.cost_usd == 0.03
    assert combined.input_tokens == 200
    assert combined.output_tokens == 40
    assert combined.latency_ms == 200.0
    assert combined.model == "claude-haiku-4-5"


def test_combine_empty_list_is_zero():
    combined = combine([])
    assert combined.cost_usd == 0.0
    assert combined.input_tokens == 0


def test_trajectory_round_trip():
    step = TrajectoryStep(
        step_index=0,
        reasoning_text="looking up the order",
        tool_call=ToolCall(
            tool_name="lookup_order", tool_input={"order_id": "ORD-1"}, tool_use_id="t1"
        ),
        tool_result=ToolResult(tool_use_id="t1", content={"amount": 100}, is_error=False),
    )
    traj = Trajectory(
        trajectory_id="traj-1",
        task_id="refunds_001_large_amount",
        steps=[step],
        final_summary="done",
        ground_truth_correct=True,
        cost_record=_cost(),
    )
    assert Trajectory.from_dict(traj.to_dict()) == traj


def test_trajectory_round_trip_with_no_cost_record():
    traj = Trajectory(
        trajectory_id="traj-2", task_id="t", steps=[], final_summary="", ground_truth_correct=False
    )
    assert Trajectory.from_dict(traj.to_dict()) == traj


def test_mutation_round_trip():
    mutation = Mutation(
        mutation_id="mut-1",
        error_type=ErrorType.TOOL_MISUSE,
        severity=Severity.BLATANT,
        target_step_index=2,
        description="changed order_id",
        original_trajectory_id="traj-1",
    )
    assert Mutation.from_dict(mutation.to_dict()) == mutation


def test_mutated_trajectory_round_trip():
    traj = Trajectory(
        trajectory_id="traj-3", task_id="t", steps=[], final_summary="", ground_truth_correct=False
    )
    mutation = Mutation(
        mutation_id="mut-2",
        error_type=ErrorType.OMISSION,
        severity=Severity.SUBTLE,
        target_step_index=1,
        description="removed override",
        original_trajectory_id="traj-orig",
    )
    unit = MutatedTrajectory(trajectory=traj, mutation=mutation, is_mutated=True)
    assert MutatedTrajectory.from_dict(unit.to_dict()) == unit


def test_mutated_trajectory_control_round_trip():
    traj = Trajectory(
        trajectory_id="traj-4", task_id="t", steps=[], final_summary="", ground_truth_correct=True
    )
    unit = MutatedTrajectory(trajectory=traj, mutation=None, is_mutated=False)
    round_tripped = MutatedTrajectory.from_dict(unit.to_dict())
    assert round_tripped == unit
    assert round_tripped.mutation is None


def test_monitor_verdict_round_trip():
    verdict = MonitorVerdict(
        verdict_id="verdict-1",
        strategy_name="full_review",
        trajectory_id="traj-1",
        flagged=True,
        confidence=0.8,
        cost_record=_cost(),
        budget=None,
        localized_step_index=2,
        raw_response_text="{}",
        flagged_at_step_index=None,
    )
    assert MonitorVerdict.from_dict(verdict.to_dict()) == verdict
