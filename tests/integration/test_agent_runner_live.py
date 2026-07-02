from __future__ import annotations

from .conftest import requires_api_key


@requires_api_key
def test_run_agent_against_a_real_task_produces_a_priced_trajectory():
    import anthropic

    from auditcurve.agent.runner import run_agent
    from auditcurve.cost.pricing import load_pricing_table
    from auditcurve.tasks.registry import get_task

    client = anthropic.Anthropic()
    pricing_table = load_pricing_table()
    task = get_task("refunds_002_small_amount")

    trajectory = run_agent(client, task, "claude-sonnet-5", pricing_table)

    assert trajectory.task_id == task.task_id
    assert trajectory.cost_record is not None
    assert trajectory.cost_record.cost_usd > 0
    # loosely: the evaluator should at least run without crashing on a live trajectory
    result = task.evaluator(trajectory, task.initial_state)
    assert isinstance(result.correct, bool)
