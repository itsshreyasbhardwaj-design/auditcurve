import datetime as dt

import pytest

from auditcurve.cost.pricing import ModelPricing, load_pricing_table


def test_load_pricing_table_loads_the_real_config():
    table = load_pricing_table()
    assert table.last_updated
    for model in ("claude-opus-4-8", "claude-sonnet-5", "claude-haiku-4-5"):
        assert model in table.models


def test_get_raises_clear_error_for_unknown_model():
    table = load_pricing_table()
    with pytest.raises(ValueError, match="claude-does-not-exist"):
        table.get("claude-does-not-exist")


def test_effective_rates_without_intro_pricing():
    pricing = ModelPricing(input_per_mtok_usd=1.0, output_per_mtok_usd=5.0)
    assert pricing.effective_rates() == (1.0, 5.0)


def test_effective_rates_uses_intro_pricing_before_expiry():
    pricing = ModelPricing(
        input_per_mtok_usd=3.0,
        output_per_mtok_usd=15.0,
        intro_input_per_mtok_usd=2.0,
        intro_output_per_mtok_usd=10.0,
        intro_expires="2026-08-31",
    )
    as_of = dt.date(2026, 7, 1)
    assert pricing.effective_rates(as_of=as_of) == (2.0, 10.0)


def test_effective_rates_falls_back_after_expiry():
    pricing = ModelPricing(
        input_per_mtok_usd=3.0,
        output_per_mtok_usd=15.0,
        intro_input_per_mtok_usd=2.0,
        intro_output_per_mtok_usd=10.0,
        intro_expires="2026-08-31",
    )
    as_of = dt.date(2026, 9, 1)
    assert pricing.effective_rates(as_of=as_of) == (3.0, 15.0)
