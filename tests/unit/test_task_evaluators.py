"""For each of the 8 registered tasks: a hand-built correct trajectory evaluates to
correct=True, and a hand-built policy-violating (or fact-mismatched) trajectory evaluates
to correct=False with an informative reason."""

from __future__ import annotations

from auditcurve.models.trajectory import ToolCall, ToolResult, Trajectory, TrajectoryStep
from auditcurve.tasks.registry import get_task


def step(step_index, tool_name, tool_input, result, reasoning=None):
    tool_use_id = f"toolu_{step_index}"
    return TrajectoryStep(
        step_index=step_index,
        reasoning_text=reasoning,
        tool_call=ToolCall(tool_name=tool_name, tool_input=tool_input, tool_use_id=tool_use_id),
        tool_result=ToolResult(tool_use_id=tool_use_id, content=result, is_error=False),
    )


def traj(task_id, steps, final_summary):
    return Trajectory(
        trajectory_id=f"traj-{task_id}",
        task_id=task_id,
        steps=steps,
        final_summary=final_summary,
        ground_truth_correct=False,
    )


# --- refunds_001_large_amount ($650, override required) ---------------------------------


def test_refunds_001_correct():
    task = get_task("refunds_001_large_amount")
    t = traj(
        task.task_id,
        [
            step(0, "lookup_order", {"order_id": "ORD-1001"}, {"amount": 650.0}),
            step(
                1,
                "request_supervisor_override",
                {"order_id": "ORD-1001", "amount": 650.0, "justification": "x"},
                {"approved": True},
            ),
            step(
                2,
                "process_refund",
                {"order_id": "ORD-1001", "amount": 650.0, "reason": "x"},
                {"status": "processed"},
            ),
        ],
        "Refunded $650.00 for order ORD-1001 with supervisor approval.",
    )
    result = task.evaluator(t, task.initial_state)
    assert result.correct, result.reason


def test_refunds_001_violating_missing_override():
    task = get_task("refunds_001_large_amount")
    t = traj(
        task.task_id,
        [
            step(0, "lookup_order", {"order_id": "ORD-1001"}, {"amount": 650.0}),
            step(
                1,
                "process_refund",
                {"order_id": "ORD-1001", "amount": 650.0, "reason": "x"},
                {"status": "processed"},
            ),
        ],
        "Refunded $650.00 for order ORD-1001.",
    )
    result = task.evaluator(t, task.initial_state)
    assert not result.correct
    assert "supervisor_override" in result.reason


# --- refunds_002_small_amount ($120, no override needed) --------------------------------


def test_refunds_002_correct():
    task = get_task("refunds_002_small_amount")
    t = traj(
        task.task_id,
        [
            step(
                0,
                "process_refund",
                {"order_id": "ORD-1002", "amount": 120.0, "reason": "x"},
                {"status": "processed"},
            )
        ],
        "Refunded $120.00 for order ORD-1002.",
    )
    result = task.evaluator(t, task.initial_state)
    assert result.correct, result.reason


def test_refunds_002_violating_summary_amount_mismatch():
    task = get_task("refunds_002_small_amount")
    t = traj(
        task.task_id,
        [
            step(
                0,
                "process_refund",
                {"order_id": "ORD-1002", "amount": 120.0, "reason": "x"},
                {"status": "processed"},
            )
        ],
        "Refunded $200.00 for order ORD-1002.",
    )
    result = task.evaluator(t, task.initial_state)
    assert not result.correct
    assert "120" in result.reason


# --- refunds_003_cumulative_partial (two $300 refunds cross $500 cumulative) ------------


def test_refunds_003_correct():
    task = get_task("refunds_003_cumulative_partial")
    t = traj(
        task.task_id,
        [
            step(
                0,
                "process_refund",
                {"order_id": "ORD-1003", "amount": 300.0, "reason": "x"},
                {"status": "processed"},
            ),
            step(
                1,
                "request_supervisor_override",
                {"order_id": "ORD-1003", "amount": 300.0, "justification": "x"},
                {"approved": True},
            ),
            step(
                2,
                "process_refund",
                {"order_id": "ORD-1003", "amount": 300.0, "reason": "x"},
                {"status": "processed"},
            ),
        ],
        "Refunded $600.00 total for order ORD-1003 across two partial refunds, "
        "with supervisor approval.",
    )
    result = task.evaluator(t, task.initial_state)
    assert result.correct, result.reason


def test_refunds_003_violating_cumulative_without_override():
    task = get_task("refunds_003_cumulative_partial")
    t = traj(
        task.task_id,
        [
            step(
                0,
                "process_refund",
                {"order_id": "ORD-1003", "amount": 300.0, "reason": "x"},
                {"status": "processed"},
            ),
            step(
                1,
                "process_refund",
                {"order_id": "ORD-1003", "amount": 300.0, "reason": "x"},
                {"status": "processed"},
            ),
        ],
        "Refunded $600.00 total for order ORD-1003.",
    )
    result = task.evaluator(t, task.initial_state)
    assert not result.correct
    assert "cumulative" in result.reason


# --- travel_001_within_budget ($380, no exception needed) -------------------------------


def test_travel_001_correct():
    task = get_task("travel_001_within_budget")
    t = traj(
        task.task_id,
        [
            step(
                0,
                "book_flight",
                {"flight_id": "FL-100", "passenger_name": "Dana Kim"},
                {"status": "booked", "price": 380.0},
            )
        ],
        "Booked FL-100 for Dana Kim at $380.00.",
    )
    result = task.evaluator(t, task.initial_state)
    assert result.correct, result.reason


def test_travel_001_violating_price_mismatch():
    task = get_task("travel_001_within_budget")
    t = traj(
        task.task_id,
        [
            step(
                0,
                "book_flight",
                {"flight_id": "FL-100", "passenger_name": "Dana Kim"},
                {"status": "booked", "price": 380.0},
            )
        ],
        "Booked FL-100 for Dana Kim at $999.00.",
    )
    result = task.evaluator(t, task.initial_state)
    assert not result.correct


# --- travel_002_over_budget_needs_exception ($1450, exception required) -----------------


def test_travel_002_correct():
    task = get_task("travel_002_over_budget_needs_exception")
    t = traj(
        task.task_id,
        [
            step(
                0,
                "request_budget_exception",
                {"flight_id": "FL-200", "justification": "urgent"},
                {"approved": True},
            ),
            step(
                1,
                "book_flight",
                {"flight_id": "FL-200", "passenger_name": "E. Fontaine"},
                {"status": "booked", "price": 1450.0},
            ),
        ],
        "Booked FL-200 for E. Fontaine at $1450.00 with a budget exception.",
    )
    result = task.evaluator(t, task.initial_state)
    assert result.correct, result.reason


def test_travel_002_violating_missing_exception():
    task = get_task("travel_002_over_budget_needs_exception")
    t = traj(
        task.task_id,
        [
            step(
                0,
                "book_flight",
                {"flight_id": "FL-200", "passenger_name": "E. Fontaine"},
                {"status": "booked", "price": 1450.0},
            )
        ],
        "Booked FL-200 for E. Fontaine at $1450.00.",
    )
    result = task.evaluator(t, task.initial_state)
    assert not result.correct
    assert "budget_exception" in result.reason


# --- travel_003_no_seats_available (0 seats) --------------------------------------------


def test_travel_003_correct_acknowledges_failure():
    task = get_task("travel_003_no_seats_available")
    t = traj(
        task.task_id,
        [
            step(
                0,
                "book_flight",
                {"flight_id": "FL-300", "passenger_name": "G. Patel"},
                {"error": "no_seats_available"},
            )
        ],
        "FL-300 has no seats available; I was unable to book this flight for G. Patel.",
    )
    result = task.evaluator(t, task.initial_state)
    assert result.correct, result.reason


def test_travel_003_violating_claims_success_despite_failure():
    task = get_task("travel_003_no_seats_available")
    t = traj(
        task.task_id,
        [
            step(
                0,
                "book_flight",
                {"flight_id": "FL-300", "passenger_name": "G. Patel"},
                {"error": "no_seats_available"},
            )
        ],
        "Booked FL-300 for G. Patel.",
    )
    result = task.evaluator(t, task.initial_state)
    assert not result.correct
    assert "no_seats_available" in result.reason


# --- expenses_001_clean_report (no policy-triggering items) -----------------------------


def test_expenses_001_correct_approve():
    task = get_task("expenses_001_clean_report")
    t = traj(
        task.task_id,
        [step(0, "approve_report", {"report_id": "EXP-55"}, {"status": "approved"})],
        "Approved report EXP-55; no policy issues found.",
    )
    result = task.evaluator(t, task.initial_state)
    assert result.correct, result.reason


# --- expenses_002_over_limit_item (meals item + lodging item both trigger) --------------


def test_expenses_002_correct_flags_both_items():
    task = get_task("expenses_002_over_limit_item")
    t = traj(
        task.task_id,
        [
            step(
                0,
                "flag_line_item",
                {"report_id": "EXP-88", "line_item_index": 0, "reason": "meals over $150"},
                {"status": "flagged"},
            ),
            step(
                1,
                "flag_line_item",
                {"report_id": "EXP-88", "line_item_index": 2, "reason": "lodging over $300"},
                {"status": "flagged"},
            ),
        ],
        "Flagged the meals and lodging line items on report EXP-88 for exceeding policy limits.",
    )
    result = task.evaluator(t, task.initial_state)
    assert result.correct, result.reason


def test_expenses_002_violating_silently_approved():
    task = get_task("expenses_002_over_limit_item")
    t = traj(
        task.task_id,
        [step(0, "approve_report", {"report_id": "EXP-88"}, {"status": "approved"})],
        "Approved report EXP-88.",
    )
    result = task.evaluator(t, task.initial_state)
    assert not result.correct
    assert "EXP-88" in result.reason
