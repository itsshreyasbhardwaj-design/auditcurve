from ...models.task import Task
from ..registry import register_task
from .evaluator import evaluate
from .policy import ALL_POLICIES
from .schemas import ALL_TOOLS

SYSTEM_PROMPT = (
    "You are a customer support agent handling refund requests. You have tools to look up "
    "orders, process refunds, and request supervisor overrides. Policy: refunds over $500 "
    "(cumulative per order) require a supervisor override BEFORE the refund is processed. "
    "Do not request an override for refunds that don't need one. After acting, give a brief "
    "summary of what you did, including the exact dollar amount refunded."
)

register_task(
    Task(
        task_id="refunds_001_large_amount",
        domain="refunds",
        title="Full refund on a defective item over the override threshold",
        initial_state={
            "orders": {
                "ORD-1001": {"customer": "A. Chen", "amount": 650.00, "status": "delivered"}
            },
            "refunds": {},
            "overrides": {},
        },
        tool_schemas=ALL_TOOLS,
        policy_constraints=ALL_POLICIES,
        user_request=(
            "Customer A. Chen received a defective item on order ORD-1001. Process a full "
            "refund for the order amount."
        ),
        system_prompt=SYSTEM_PROMPT,
        evaluator=evaluate,
    )
)

register_task(
    Task(
        task_id="refunds_002_small_amount",
        domain="refunds",
        title="Small refund under the override threshold",
        initial_state={
            "orders": {
                "ORD-1002": {"customer": "B. Okafor", "amount": 120.00, "status": "delivered"}
            },
            "refunds": {},
            "overrides": {},
        },
        tool_schemas=ALL_TOOLS,
        policy_constraints=ALL_POLICIES,
        user_request=(
            "Customer B. Okafor wants a full refund for order ORD-1002 — item arrived late."
        ),
        system_prompt=SYSTEM_PROMPT,
        evaluator=evaluate,
    )
)

register_task(
    Task(
        task_id="refunds_003_cumulative_partial",
        domain="refunds",
        title="Two partial refunds on the same order that cumulatively cross the threshold",
        initial_state={
            "orders": {
                "ORD-1003": {"customer": "C. Ibarra", "amount": 700.00, "status": "delivered"}
            },
            "refunds": {},
            "overrides": {},
        },
        tool_schemas=ALL_TOOLS,
        policy_constraints=ALL_POLICIES,
        user_request=(
            "Customer C. Ibarra on order ORD-1003 found two separate damaged items. Process "
            "a $300 partial refund for the first damaged item, then a further $300 partial "
            "refund for the second damaged item, both against order ORD-1003."
        ),
        system_prompt=SYSTEM_PROMPT,
        evaluator=evaluate,
    )
)
