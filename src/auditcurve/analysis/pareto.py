"""Aggregates per-(strategy, budget) cost/latency/F1 and computes the Pareto frontier — the
headline result. Standard O(n log n) skyline: sort by the cost axis ascending, keep points
that strictly beat the running-max F1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..models.mutation import MutatedTrajectory
from ..models.verdict import MonitorVerdict
from .metrics import ConfusionCounts, classify_verdict, precision_recall_f1


@dataclass(frozen=True)
class StrategyPoint:
    strategy_name: str
    budget: int | None
    mean_cost_usd: float
    mean_latency_ms: float
    f1: float
    n: int


def aggregate_strategy_points(
    verdicts: list[MonitorVerdict], mutations: list[MutatedTrajectory]
) -> list[StrategyPoint]:
    lookup = {m.trajectory.trajectory_id: m for m in mutations}
    groups: dict[tuple[str, int | None], list[MonitorVerdict]] = {}
    for v in verdicts:
        groups.setdefault((v.strategy_name, v.budget), []).append(v)

    points = []
    for (strategy_name, budget), vs in groups.items():
        counts = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
        costs, latencies = [], []
        for v in vs:
            unit = lookup.get(v.trajectory_id)
            if unit is None:
                continue
            counts[classify_verdict(unit, v)] += 1
            costs.append(v.cost_record.cost_usd)
            latencies.append(v.cost_record.latency_ms)

        _, _, f1 = precision_recall_f1(ConfusionCounts(**counts))
        points.append(
            StrategyPoint(
                strategy_name=strategy_name,
                budget=budget,
                mean_cost_usd=sum(costs) / len(costs) if costs else 0.0,
                mean_latency_ms=sum(latencies) / len(latencies) if latencies else 0.0,
                f1=f1,
                n=len(vs),
            )
        )
    return points


def pareto_frontier(
    points: list[StrategyPoint], cost_axis: Literal["cost", "latency"]
) -> list[StrategyPoint]:
    key_fn = (lambda p: p.mean_cost_usd) if cost_axis == "cost" else (lambda p: p.mean_latency_ms)
    frontier = []
    best_f1 = -1.0
    for p in sorted(points, key=key_fn):
        if p.f1 > best_f1:
            frontier.append(p)
            best_f1 = p.f1
    return frontier
