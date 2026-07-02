"""CostRecord: the one place a real API call's token usage, latency, and dollar cost live."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CostRecord:
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float
    timestamp: str
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    request_id: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> CostRecord:
        return CostRecord(**data)


ZERO_COST = CostRecord(
    model="none",
    input_tokens=0,
    output_tokens=0,
    cost_usd=0.0,
    latency_ms=0.0,
    timestamp="",
)


def combine(records: list[CostRecord]) -> CostRecord:
    """Sums tokens/cost/latency across multiple calls (e.g. a multi-turn agent run or a
    multi-phase monitor strategy). The resulting `model` field lists every distinct model
    used, comma-joined, since a combined record may span both untrusted and trusted models."""
    if not records:
        return ZERO_COST

    models = ",".join(sorted({r.model for r in records}))
    return CostRecord(
        model=models,
        input_tokens=sum(r.input_tokens for r in records),
        output_tokens=sum(r.output_tokens for r in records),
        cost_usd=sum(r.cost_usd for r in records),
        latency_ms=sum(r.latency_ms for r in records),
        timestamp=records[-1].timestamp,
        cache_read_input_tokens=sum(r.cache_read_input_tokens for r in records),
        cache_creation_input_tokens=sum(r.cache_creation_input_tokens for r in records),
        request_id=None,
    )
