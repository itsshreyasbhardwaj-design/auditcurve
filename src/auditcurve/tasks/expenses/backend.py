"""Deterministic in-memory mock backend for the expense-auditing domain. No network calls."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def get_expense_report(state: dict[str, Any], report_id: str) -> dict[str, Any]:
    report = state["reports"].get(report_id)
    if report is None:
        return {"error": "not_found", "report_id": report_id}
    return {"report_id": report_id, **report}


def flag_line_item(
    state: dict[str, Any], report_id: str, line_item_index: int, reason: str
) -> dict[str, Any]:
    state["flags"].setdefault(report_id, []).append(
        {"line_item_index": line_item_index, "reason": reason}
    )
    return {"status": "flagged", "report_id": report_id, "line_item_index": line_item_index}


def approve_report(state: dict[str, Any], report_id: str) -> dict[str, Any]:
    state["approvals"][report_id] = {"status": "approved"}
    return {"status": "approved", "report_id": report_id}


def escalate_to_finance(state: dict[str, Any], report_id: str, reason: str) -> dict[str, Any]:
    state["escalations"][report_id] = {"reason": reason}
    return {"status": "escalated", "report_id": report_id}


_DISPATCH_TABLE: dict[str, Callable[..., dict[str, Any]]] = {
    "get_expense_report": get_expense_report,
    "flag_line_item": flag_line_item,
    "approve_report": approve_report,
    "escalate_to_finance": escalate_to_finance,
}


def dispatch(state: dict[str, Any], tool_name: str, tool_input: dict[str, Any]) -> Any:
    fn = _DISPATCH_TABLE.get(tool_name)
    if fn is None:
        return {"error": "unknown_tool", "tool_name": tool_name}
    return fn(state, **tool_input)
