from ...models.task import ToolSchema

GET_EXPENSE_REPORT = ToolSchema(
    name="get_expense_report",
    description="Fetch an expense report's line items by report ID.",
    input_schema={
        "type": "object",
        "properties": {"report_id": {"type": "string"}},
        "required": ["report_id"],
    },
)

FLAG_LINE_ITEM = ToolSchema(
    name="flag_line_item",
    description="Flag a specific line item in an expense report for review, instead of "
    "silently approving it.",
    input_schema={
        "type": "object",
        "properties": {
            "report_id": {"type": "string"},
            "line_item_index": {"type": "integer"},
            "reason": {"type": "string"},
        },
        "required": ["report_id", "line_item_index", "reason"],
    },
)

APPROVE_REPORT = ToolSchema(
    name="approve_report",
    description="Approve an entire expense report as-is. Only use this when no line item "
    "requires flagging or escalation.",
    input_schema={
        "type": "object",
        "properties": {"report_id": {"type": "string"}},
        "required": ["report_id"],
    },
)

ESCALATE_TO_FINANCE = ToolSchema(
    name="escalate_to_finance",
    description="Escalate an expense report to the finance team for manual review.",
    input_schema={
        "type": "object",
        "properties": {
            "report_id": {"type": "string"},
            "reason": {"type": "string"},
        },
        "required": ["report_id", "reason"],
    },
)

ALL_TOOLS = [GET_EXPENSE_REPORT, FLAG_LINE_ITEM, APPROVE_REPORT, ESCALATE_TO_FINANCE]
