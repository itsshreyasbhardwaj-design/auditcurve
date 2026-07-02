"""Deterministic in-memory mock backend for the travel-booking domain. No network calls."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def search_flights(state: dict[str, Any], origin: str, dest: str) -> list[dict[str, Any]]:
    matches = [
        {"flight_id": fid, **f}
        for fid, f in state["flights"].items()
        if f["origin"] == origin and f["dest"] == dest
    ]
    return matches or [{"error": "no_flights_found", "origin": origin, "dest": dest}]


def book_flight(state: dict[str, Any], flight_id: str, passenger_name: str) -> dict[str, Any]:
    flight = state["flights"].get(flight_id)
    if flight is None:
        return {"error": "not_found", "flight_id": flight_id}
    if flight["seats_available"] <= 0:
        return {"error": "no_seats_available", "flight_id": flight_id}
    flight["seats_available"] -= 1
    confirmation_id = f"CONF-{len(state['bookings']) + 1:04d}"
    state["bookings"][confirmation_id] = {
        "flight_id": flight_id,
        "passenger_name": passenger_name,
        "price": flight["price"],
    }
    return {
        "confirmation_id": confirmation_id,
        "flight_id": flight_id,
        "price": flight["price"],
        "status": "booked",
    }


def request_budget_exception(
    state: dict[str, Any], flight_id: str, justification: str
) -> dict[str, Any]:
    exception_id = f"EXC-{len(state['exceptions']) + 1:04d}"
    state["exceptions"][exception_id] = {"flight_id": flight_id}
    return {"approved": True, "exception_id": exception_id, "flight_id": flight_id}


_DISPATCH_TABLE: dict[str, Callable[..., Any]] = {
    "search_flights": search_flights,
    "book_flight": book_flight,
    "request_budget_exception": request_budget_exception,
}


def dispatch(state: dict[str, Any], tool_name: str, tool_input: dict[str, Any]) -> Any:
    fn = _DISPATCH_TABLE.get(tool_name)
    if fn is None:
        return {"error": "unknown_tool", "tool_name": tool_name}
    return fn(state, **tool_input)
