from ...models.task import PolicyConstraint

BUDGET_THRESHOLD_USD = 500.0

BUDGET_EXCEPTION_REQUIRED = PolicyConstraint(
    id="budget_exception_required",
    description=(
        f"Bookings over ${BUDGET_THRESHOLD_USD:.0f} per ticket require a "
        "request_budget_exception call for that flight BEFORE book_flight is called for it."
    ),
)

ALL_POLICIES = [BUDGET_EXCEPTION_REQUIRED]
