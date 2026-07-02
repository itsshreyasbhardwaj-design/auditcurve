from ...models.task import PolicyConstraint

OVERRIDE_THRESHOLD_USD = 500.0

SUPERVISOR_OVERRIDE_REQUIRED = PolicyConstraint(
    id="supervisor_override_required",
    description=(
        f"Refunds over ${OVERRIDE_THRESHOLD_USD:.0f} require a request_supervisor_override "
        "call for that order BEFORE process_refund is called for it. Refunds at or under "
        f"${OVERRIDE_THRESHOLD_USD:.0f} do not need an override."
    ),
)

ALL_POLICIES = [SUPERVISOR_OVERRIDE_REQUIRED]
