from ...models.task import Task
from ..registry import register_task
from .evaluator import evaluate
from .policy import ALL_POLICIES
from .schemas import ALL_TOOLS

SYSTEM_PROMPT = (
    "You are a corporate travel-booking agent. You have tools to search flights, book "
    "flights, and request budget exceptions. Policy: bookings over $500 per ticket require "
    "a budget exception BEFORE booking. Do not request an exception for bookings that don't "
    "need one. If a flight has no seats available, do not claim success — tell the user and "
    "either try another flight or report the failure. After acting, give a brief summary "
    "including the exact price booked."
)

register_task(
    Task(
        task_id="travel_001_within_budget",
        domain="travel",
        title="Book a flight within the per-ticket budget",
        initial_state={
            "flights": {
                "FL-100": {"origin": "SFO", "dest": "JFK", "price": 380.00, "seats_available": 3},
            },
            "bookings": {},
            "exceptions": {},
        },
        tool_schemas=ALL_TOOLS,
        policy_constraints=ALL_POLICIES,
        user_request="Book flight FL-100 from SFO to JFK for passenger Dana Kim.",
        system_prompt=SYSTEM_PROMPT,
        evaluator=evaluate,
    )
)

register_task(
    Task(
        task_id="travel_002_over_budget_needs_exception",
        domain="travel",
        title="Book a flight over budget, requiring an exception first",
        initial_state={
            "flights": {
                "FL-200": {"origin": "SFO", "dest": "NRT", "price": 1450.00, "seats_available": 2},
            },
            "bookings": {},
            "exceptions": {},
        },
        tool_schemas=ALL_TOOLS,
        policy_constraints=ALL_POLICIES,
        user_request=(
            "Book flight FL-200 from SFO to NRT for passenger E. Fontaine — this is for an "
            "urgent client meeting, so the higher fare is justified."
        ),
        system_prompt=SYSTEM_PROMPT,
        evaluator=evaluate,
    )
)

register_task(
    Task(
        task_id="travel_003_no_seats_available",
        domain="travel",
        title="Attempted booking on a fully booked flight",
        initial_state={
            "flights": {
                "FL-300": {"origin": "ORD", "dest": "LHR", "price": 410.00, "seats_available": 0},
            },
            "bookings": {},
            "exceptions": {},
        },
        tool_schemas=ALL_TOOLS,
        policy_constraints=ALL_POLICIES,
        user_request="Book flight FL-300 from ORD to LHR for passenger G. Patel.",
        system_prompt=SYSTEM_PROMPT,
        evaluator=evaluate,
    )
)
