"""Routes a task's tool_use blocks to that task's domain-specific mock backend."""

from __future__ import annotations

from ..tasks.expenses import backend as expenses_backend
from ..tasks.refunds import backend as refunds_backend
from ..tasks.registry import Dispatch
from ..tasks.travel import backend as travel_backend

_DOMAIN_DISPATCH: dict[str, Dispatch] = {
    "refunds": refunds_backend.dispatch,
    "travel": travel_backend.dispatch,
    "expenses": expenses_backend.dispatch,
}


def get_dispatch_for_domain(domain: str) -> Dispatch:
    try:
        return _DOMAIN_DISPATCH[domain]
    except KeyError:
        raise ValueError(f"No mock backend registered for domain '{domain}'") from None
