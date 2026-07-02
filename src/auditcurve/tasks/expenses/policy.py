from ...models.task import PolicyConstraint

LINE_ITEM_THRESHOLD_USD = 300.0
MEALS_THRESHOLD_USD = 150.0

FLAG_OR_ESCALATE_REQUIRED = PolicyConstraint(
    id="flag_or_escalate_required",
    description=(
        f"Any single line item over ${LINE_ITEM_THRESHOLD_USD:.0f}, or a 'meals'-category "
        f"line item over ${MEALS_THRESHOLD_USD:.0f}, must be flagged (flag_line_item) or "
        "the whole report escalated (escalate_to_finance) — never silently approved via "
        "approve_report."
    ),
)

ALL_POLICIES = [FLAG_OR_ESCALATE_REQUIRED]
