"""Loads and validates pricing_config.yaml. Fails loud (raises) rather than silently
defaulting when a model used in an experiment isn't in the table — a missing price must
never be misread as a free call."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_PATH = Path(__file__).parent / "pricing_config.yaml"


@dataclass(frozen=True)
class ModelPricing:
    input_per_mtok_usd: float
    output_per_mtok_usd: float
    intro_input_per_mtok_usd: float | None = None
    intro_output_per_mtok_usd: float | None = None
    intro_expires: str | None = None

    def effective_rates(self, as_of: dt.date | None = None) -> tuple[float, float]:
        """Returns (input_rate, output_rate), applying the intro discount if it hasn't
        expired as of `as_of` (defaults to today)."""
        if self.intro_input_per_mtok_usd is None or self.intro_expires is None:
            return self.input_per_mtok_usd, self.output_per_mtok_usd
        as_of = as_of or dt.date.today()
        expires = dt.date.fromisoformat(self.intro_expires)
        if as_of <= expires:
            return (
                self.intro_input_per_mtok_usd,
                self.intro_output_per_mtok_usd or self.output_per_mtok_usd,
            )
        return self.input_per_mtok_usd, self.output_per_mtok_usd


@dataclass(frozen=True)
class PricingTable:
    last_updated: str
    models: dict[str, ModelPricing]
    cache_write_5m_multiplier: float
    cache_write_1h_multiplier: float
    cache_read_multiplier: float

    def get(self, model: str) -> ModelPricing:
        try:
            return self.models[model]
        except KeyError:
            raise ValueError(
                f"No pricing entry for model '{model}' in {DEFAULT_PATH.name} "
                f"(last updated {self.last_updated}). Add it before running an experiment "
                "that uses this model — never assume a default price."
            ) from None


def load_pricing_table(path: Path | None = None) -> PricingTable:
    path = path or DEFAULT_PATH
    raw = yaml.safe_load(path.read_text())

    if "last_updated" not in raw:
        raise ValueError(f"{path} is missing the required 'last_updated' field")

    models = {
        name: ModelPricing(
            input_per_mtok_usd=cfg["input_per_mtok_usd"],
            output_per_mtok_usd=cfg["output_per_mtok_usd"],
            intro_input_per_mtok_usd=cfg.get("intro_input_per_mtok_usd"),
            intro_output_per_mtok_usd=cfg.get("intro_output_per_mtok_usd"),
            intro_expires=cfg.get("intro_expires"),
        )
        for name, cfg in raw["models"].items()
    }

    cache_cfg = raw.get("cache", {})
    return PricingTable(
        last_updated=raw["last_updated"],
        models=models,
        cache_write_5m_multiplier=cache_cfg.get("cache_write_5m_multiplier", 1.25),
        cache_write_1h_multiplier=cache_cfg.get("cache_write_1h_multiplier", 2.0),
        cache_read_multiplier=cache_cfg.get("cache_read_multiplier", 0.10),
    )
