from types import SimpleNamespace

from auditcurve.cost.calculator import compute_cost, record_api_call
from auditcurve.cost.pricing import ModelPricing, PricingTable


def make_table() -> PricingTable:
    return PricingTable(
        last_updated="2026-06-24",
        models={
            "claude-sonnet-5": ModelPricing(input_per_mtok_usd=3.0, output_per_mtok_usd=15.0),
            "claude-haiku-4-5": ModelPricing(input_per_mtok_usd=1.0, output_per_mtok_usd=5.0),
        },
        cache_write_5m_multiplier=1.25,
        cache_write_1h_multiplier=2.0,
        cache_read_multiplier=0.10,
    )


def test_compute_cost_matches_hand_calculation():
    table = make_table()
    # 1,000,000 input tokens at $3/Mtok + 1,000,000 output tokens at $15/Mtok = $18
    cost = compute_cost("claude-sonnet-5", 1_000_000, 1_000_000, table)
    assert cost == 18.0


def test_compute_cost_small_amounts():
    table = make_table()
    # 1000 input tokens = 0.001 Mtok * $1/Mtok = $0.001; 200 output tokens = 0.0002*$5=$0.001
    cost = compute_cost("claude-haiku-4-5", 1000, 200, table)
    assert round(cost, 6) == round(0.001 + 0.001, 6)


def test_compute_cost_applies_cache_multipliers():
    table = make_table()
    # cache_read: 1,000,000 tokens * $1/Mtok * 0.10 = $0.10
    cost = compute_cost("claude-haiku-4-5", 0, 0, table, cache_read_tokens=1_000_000)
    assert cost == 0.10

    # cache_creation: 1,000,000 tokens * $1/Mtok * 1.25 = $1.25
    cost = compute_cost("claude-haiku-4-5", 0, 0, table, cache_creation_tokens=1_000_000)
    assert cost == 1.25


def test_compute_cost_unknown_model_raises():
    table = make_table()
    try:
        compute_cost("claude-unknown-model", 100, 100, table)
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "claude-unknown-model" in str(e)


def test_record_api_call_reads_usage_and_computes_cost():
    table = make_table()
    fake_usage = SimpleNamespace(
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        cache_read_input_tokens=0,
        cache_creation_input_tokens=0,
    )
    fake_response = SimpleNamespace(usage=fake_usage, _request_id="req_123")

    record = record_api_call("claude-sonnet-5", fake_response, latency_ms=42.0, pricing_table=table)

    assert record.cost_usd == 18.0
    assert record.input_tokens == 1_000_000
    assert record.output_tokens == 1_000_000
    assert record.latency_ms == 42.0
    assert record.request_id == "req_123"
    assert record.model == "claude-sonnet-5"
