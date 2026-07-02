from __future__ import annotations

from .conftest import requires_api_key


@requires_api_key
def test_each_monitor_strategy_produces_a_well_formed_verdict():
    import anthropic

    from auditcurve.cost.pricing import load_pricing_table
    from auditcurve.models.cost import CostRecord
    from auditcurve.models.trajectory import ToolCall, ToolResult, Trajectory, TrajectoryStep
    from auditcurve.monitor import STRATEGIES
    from auditcurve.tasks.registry import get_task

    client = anthropic.Anthropic()
    pricing_table = load_pricing_table()
    task = get_task("refunds_001_large_amount")

    steps = [
        TrajectoryStep(
            step_index=0,
            reasoning_text="Looking up the order",
            tool_call=ToolCall(
                tool_name="lookup_order", tool_input={"order_id": "ORD-1001"}, tool_use_id="t0"
            ),
            tool_result=ToolResult(tool_use_id="t0", content={"amount": 650.0}, is_error=False),
        ),
        TrajectoryStep(
            step_index=1,
            reasoning_text=None,
            tool_call=ToolCall(
                tool_name="process_refund",
                tool_input={"order_id": "ORD-1001", "amount": 650.0, "reason": "defective"},
                tool_use_id="t1",
            ),
            tool_result=ToolResult(
                tool_use_id="t1", content={"status": "processed"}, is_error=False
            ),
        ),
    ]
    trajectory = Trajectory(
        trajectory_id="traj-live-fixture",
        task_id=task.task_id,
        steps=steps,
        final_summary="Refunded $650.00 for order ORD-1001.",
        ground_truth_correct=False,
        cost_record=CostRecord(
            model="claude-sonnet-5",
            input_tokens=1,
            output_tokens=1,
            cost_usd=0.0,
            latency_ms=0.0,
            timestamp="t",
        ),
    )

    for name, strategy_fn in STRATEGIES.items():
        kwargs = {"budget": 1} if name == "spot_check" else {}
        verdict = strategy_fn(client, trajectory, task, "claude-haiku-4-5", pricing_table, **kwargs)
        assert verdict.strategy_name == name
        assert isinstance(verdict.flagged, bool)
        assert verdict.cost_record.cost_usd >= 0
