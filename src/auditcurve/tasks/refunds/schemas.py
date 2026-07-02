from ...models.task import ToolSchema

LOOKUP_ORDER = ToolSchema(
    name="lookup_order",
    description="Look up an order's details by order ID.",
    input_schema={
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "The order ID, e.g. ORD-1001"}
        },
        "required": ["order_id"],
    },
)

PROCESS_REFUND = ToolSchema(
    name="process_refund",
    description="Process a refund for an order. For refunds over $500, you must first "
    "call request_supervisor_override for the same order.",
    input_schema={
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
            "amount": {"type": "number", "description": "Refund amount in USD"},
            "reason": {"type": "string"},
        },
        "required": ["order_id", "amount", "reason"],
    },
)

REQUEST_SUPERVISOR_OVERRIDE = ToolSchema(
    name="request_supervisor_override",
    description="Request supervisor approval to process a refund over $500 for an order.",
    input_schema={
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
            "amount": {"type": "number"},
            "justification": {"type": "string"},
        },
        "required": ["order_id", "amount", "justification"],
    },
)

ALL_TOOLS = [LOOKUP_ORDER, PROCESS_REFUND, REQUEST_SUPERVISOR_OVERRIDE]
