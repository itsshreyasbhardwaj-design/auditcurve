"""Precision/recall/F1, grouped breakdowns, localization accuracy, and streaming detection
latency — all computed from persisted verdicts + mutations, never from anything hand-typed."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..models.mutation import MutatedTrajectory
from ..models.verdict import MonitorVerdict

GroupKey = Literal["error_type", "severity", "strategy", "budget"]


@dataclass(frozen=True)
class ConfusionCounts:
    tp: int
    fp: int
    fn: int
    tn: int


def _mutation_lookup(mutations: list[MutatedTrajectory]) -> dict[str, MutatedTrajectory]:
    return {m.trajectory.trajectory_id: m for m in mutations}


def classify_verdict(unit: MutatedTrajectory, verdict: MonitorVerdict) -> str:
    if unit.is_mutated and verdict.flagged:
        return "tp"
    if unit.is_mutated and not verdict.flagged:
        return "fn"
    if not unit.is_mutated and verdict.flagged:
        return "fp"
    return "tn"


def compute_confusion_counts(
    verdicts: list[MonitorVerdict], mutations: list[MutatedTrajectory]
) -> ConfusionCounts:
    lookup = _mutation_lookup(mutations)
    counts = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    for v in verdicts:
        unit = lookup.get(v.trajectory_id)
        if unit is None:
            continue
        counts[classify_verdict(unit, v)] += 1
    return ConfusionCounts(**counts)


def precision_recall_f1(counts: ConfusionCounts) -> tuple[float, float, float]:
    precision = counts.tp / (counts.tp + counts.fp) if (counts.tp + counts.fp) else 0.0
    recall = counts.tp / (counts.tp + counts.fn) if (counts.tp + counts.fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1


def _group_value(unit: MutatedTrajectory, verdict: MonitorVerdict, group_by: GroupKey):
    if group_by == "error_type":
        return unit.mutation.error_type.value if unit.mutation else "control"
    if group_by == "severity":
        return unit.mutation.severity.value if unit.mutation else "control"
    if group_by == "strategy":
        return verdict.strategy_name
    if group_by == "budget":
        return verdict.budget
    raise ValueError(f"unknown group_by: {group_by}")


def metrics_by_group(
    verdicts: list[MonitorVerdict], mutations: list[MutatedTrajectory], group_by: GroupKey
) -> dict:
    lookup = _mutation_lookup(mutations)
    grouped: dict = {}
    for v in verdicts:
        unit = lookup.get(v.trajectory_id)
        if unit is None:
            continue
        key = _group_value(unit, v, group_by)
        grouped.setdefault(key, {"tp": 0, "fp": 0, "fn": 0, "tn": 0})
        grouped[key][classify_verdict(unit, v)] += 1

    return {key: precision_recall_f1(ConfusionCounts(**counts)) for key, counts in grouped.items()}


def localization_accuracy(
    verdicts: list[MonitorVerdict], mutations: list[MutatedTrajectory]
) -> float:
    lookup = _mutation_lookup(mutations)
    correct = total = 0
    for v in verdicts:
        unit = lookup.get(v.trajectory_id)
        if unit is None or not unit.is_mutated or not v.flagged or unit.mutation is None:
            continue
        total += 1
        if v.localized_step_index == unit.mutation.target_step_index:
            correct += 1
    return correct / total if total else 0.0


def detection_latency(
    verdicts: list[MonitorVerdict], mutations: list[MutatedTrajectory]
) -> list[int]:
    """Streaming-only: flagged_at_step_index - target_step_index. 0 = flagged exactly at the
    error's step (the best realistic case); negative means flagged before it was even
    visible, which shouldn't happen and would indicate a labeling bug if seen."""
    lookup = _mutation_lookup(mutations)
    latencies = []
    for v in verdicts:
        if v.strategy_name != "streaming" or v.flagged_at_step_index is None:
            continue
        unit = lookup.get(v.trajectory_id)
        if unit is None or unit.mutation is None:
            continue
        latencies.append(v.flagged_at_step_index - unit.mutation.target_step_index)
    return latencies
