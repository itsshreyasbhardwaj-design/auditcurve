"""Turns real token usage into real dollars. Every Anthropic API call site in the codebase
goes through `timed_create()` — cost/latency capture is structural, not something each call
site can forget."""

from __future__ import annotations

import datetime as dt
import time
from typing import Any

from ..models.cost import CostRecord
from .pricing import PricingTable


def compute_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    pricing_table: PricingTable,
    cache_read_tokens: int = 0,
    cache_creation_tokens: int = 0,
) -> float:
    """Pure function: tokens -> USD, using the loaded pricing table."""
    pricing = pricing_table.get(model)
    input_rate, output_rate = pricing.effective_rates()

    base_input_cost = (input_tokens / 1_000_000) * input_rate
    output_cost = (output_tokens / 1_000_000) * output_rate
    cache_read_cost = (
        (cache_read_tokens / 1_000_000) * input_rate * pricing_table.cache_read_multiplier
    )
    cache_write_cost = (
        (cache_creation_tokens / 1_000_000) * input_rate * pricing_table.cache_write_5m_multiplier
    )

    return base_input_cost + output_cost + cache_read_cost + cache_write_cost


def record_api_call(
    model: str,
    response: Any,
    latency_ms: float,
    pricing_table: PricingTable,
) -> CostRecord:
    """The one place that reads response.usage.* and produces a CostRecord."""
    usage = response.usage
    input_tokens = usage.input_tokens
    output_tokens = usage.output_tokens
    cache_read_tokens = getattr(usage, "cache_read_input_tokens", 0) or 0
    cache_creation_tokens = getattr(usage, "cache_creation_input_tokens", 0) or 0

    cost_usd = compute_cost(
        model,
        input_tokens,
        output_tokens,
        pricing_table,
        cache_read_tokens=cache_read_tokens,
        cache_creation_tokens=cache_creation_tokens,
    )

    return CostRecord(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        latency_ms=latency_ms,
        timestamp=dt.datetime.now(dt.UTC).isoformat(),
        cache_read_input_tokens=cache_read_tokens,
        cache_creation_input_tokens=cache_creation_tokens,
        request_id=getattr(response, "_request_id", None),
    )


def timed_create(client: Any, pricing_table: PricingTable, **kwargs: Any) -> tuple[Any, CostRecord]:
    """Wraps client.messages.create(**kwargs), timing it and producing a CostRecord.
    Every call site (agent runner, all monitor strategies) must go through this —
    never call client.messages.create directly."""
    start = time.monotonic()
    response = client.messages.create(**kwargs)
    latency_ms = (time.monotonic() - start) * 1000
    cost_record = record_api_call(kwargs["model"], response, latency_ms, pricing_table)
    return response, cost_record
