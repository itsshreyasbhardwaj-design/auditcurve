"""Deterministic in-memory mock backend for the refunds domain. No network calls."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def lookup_order(state: dict[str, Any], order_id: str) -> dict[str, Any]:
    order = state["orders"].get(order_id)
    if order is None:
        return {"error": "not_found", "order_id": order_id}
    return {"order_id": order_id, **order}


def process_refund(
    state: dict[str, Any], order_id: str, amount: float, reason: str
) -> dict[str, Any]:
    if order_id not in state["orders"]:
        return {"error": "not_found", "order_id": order_id}
    refund_id = f"REF-{len(state['refunds']) + 1:04d}"
    state["refunds"][refund_id] = {"order_id": order_id, "amount": amount, "reason": reason}
    return {"refund_id": refund_id, "status": "processed", "order_id": order_id, "amount": amount}


def request_supervisor_override(
    state: dict[str, Any], order_id: str, amount: float, justification: str
) -> dict[str, Any]:
    override_id = f"OVR-{len(state['overrides']) + 1:04d}"
    state["overrides"][override_id] = {"order_id": order_id, "amount": amount}
    return {"approved": True, "override_id": override_id, "order_id": order_id}


_DISPATCH_TABLE: dict[str, Callable[..., dict[str, Any]]] = {
    "lookup_order": lookup_order,
    "process_refund": process_refund,
    "request_supervisor_override": request_supervisor_override,
}


def dispatch(state: dict[str, Any], tool_name: str, tool_input: dict[str, Any]) -> Any:
    fn = _DISPATCH_TABLE.get(tool_name)
    if fn is None:
        return {"error": "unknown_tool", "tool_name": tool_name}
    return fn(state, **tool_input)
