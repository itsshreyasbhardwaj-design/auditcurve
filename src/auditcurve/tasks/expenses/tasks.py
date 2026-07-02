from ...models.task import Task
from ..registry import register_task
from .evaluator import evaluate
from .policy import ALL_POLICIES
from .schemas import ALL_TOOLS

SYSTEM_PROMPT = (
    "You are an expense-report auditor. You have tools to fetch a report, flag a line "
    "item, approve a report, or escalate a report to finance. Policy: any single line item "
    "over $300, or a 'meals'-category line item over $150, must be flagged or the report "
    "escalated — never silently approved. After acting, give a brief summary of what you "
    "did and why."
)

register_task(
    Task(
        task_id="expenses_001_clean_report",
        domain="expenses",
        title="A clean report with no policy violations",
        initial_state={
            "reports": {
                "EXP-55": {
                    "employee": "R. Singh",
                    "line_items": [
                        {"category": "meals", "amount": 45.00},
                        {"category": "transport", "amount": 60.00},
                        {"category": "supplies", "amount": 120.00},
                    ],
                    "total": 225.00,
                }
            },
            "flags": {},
            "approvals": {},
            "escalations": {},
        },
        tool_schemas=ALL_TOOLS,
        policy_constraints=ALL_POLICIES,
        user_request="Audit expense report EXP-55 and take the appropriate action.",
        system_prompt=SYSTEM_PROMPT,
        evaluator=evaluate,
    )
)

register_task(
    Task(
        task_id="expenses_002_over_limit_item",
        domain="expenses",
        title="A report with one over-the-limit line item",
        initial_state={
            "reports": {
                "EXP-88": {
                    "employee": "T. Nakamura",
                    "line_items": [
                        {"category": "meals", "amount": 210.00},
                        {"category": "transport", "amount": 80.00},
                        {"category": "lodging", "amount": 340.00},
                    ],
                    "total": 630.00,
                }
            },
            "flags": {},
            "approvals": {},
            "escalations": {},
        },
        tool_schemas=ALL_TOOLS,
        policy_constraints=ALL_POLICIES,
        user_request="Audit expense report EXP-88 and take the appropriate action.",
        system_prompt=SYSTEM_PROMPT,
        evaluator=evaluate,
    )
)
