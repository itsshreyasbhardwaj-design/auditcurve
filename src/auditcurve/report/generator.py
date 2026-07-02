"""Renders REPORT.md from persisted results only — re-running analysis code every time, so
this module has no path to inventing a number that didn't come from an actual experiment."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import jinja2

from ..analysis.metrics import detection_latency, localization_accuracy, metrics_by_group
from ..analysis.pareto import aggregate_strategy_points, pareto_frontier
from ..models.mutation import MutatedTrajectory
from ..models.trajectory import Trajectory
from ..models.verdict import MonitorVerdict
from ..orchestration.persistence import read_jsonl
from ..tasks.registry import all_tasks

TEMPLATE_DIR = Path(__file__).parent / "templates"

EXPECTED_PLOTS = (
    "pareto_cost_vs_f1.png",
    "pareto_latency_vs_f1.png",
    "f1_by_category_severity.png",
)


def _load_metadata(results_dir: Path) -> dict:
    path = results_dir / "metadata.json"
    return json.loads(path.read_text()) if path.exists() else {}


def _load_summary_rows(tables_dir: Path) -> list[dict]:
    path = tables_dir / "summary_metrics.csv"
    if not path.exists():
        return []
    with path.open() as f:
        return list(csv.DictReader(f))


def generate_report(
    results_dir: Path, plots_dir: Path, tables_dir: Path, output_path: Path
) -> None:
    missing = [name for name in EXPECTED_PLOTS if not (plots_dir / name).exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing plot(s) {missing} in {plots_dir} — run `auditcurve analyze` before "
            "`auditcurve report` (the report assumes plots already exist rather than "
            "silently skipping them)."
        )

    trajectories = read_jsonl(results_dir / "trajectories.jsonl", Trajectory.from_dict)
    mutations = read_jsonl(results_dir / "mutations.jsonl", MutatedTrajectory.from_dict)
    verdicts = read_jsonl(results_dir / "verdicts.jsonl", MonitorVerdict.from_dict)
    metadata = _load_metadata(results_dir)

    points = aggregate_strategy_points(verdicts, mutations)
    frontier_cost = pareto_frontier(points, "cost")
    frontier_latency = pareto_frontier(points, "latency")

    by_error = metrics_by_group(verdicts, mutations, "error_type")
    by_severity = metrics_by_group(verdicts, mutations, "severity")
    by_strategy = metrics_by_group(verdicts, mutations, "strategy")

    loc_acc = localization_accuracy(verdicts, mutations)
    latencies = detection_latency(verdicts, mutations)
    mean_latency = sum(latencies) / len(latencies) if latencies else None

    n_mutated = sum(1 for u in mutations if u.is_mutated)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(TEMPLATE_DIR), trim_blocks=True, lstrip_blocks=True
    )
    template = env.get_template("report.md.jinja2")

    rendered = template.render(
        metadata=metadata,
        n_tasks=len(all_tasks()),
        n_trajectories=len(trajectories),
        n_correct=sum(1 for t in trajectories if t.ground_truth_correct),
        n_mutated=n_mutated,
        n_control=len(mutations) - n_mutated,
        points=sorted(points, key=lambda p: (p.strategy_name, p.budget or 0)),
        frontier_cost=frontier_cost,
        frontier_latency=frontier_latency,
        by_error=dict(sorted(by_error.items())),
        by_severity=dict(sorted(by_severity.items())),
        by_strategy=dict(sorted(by_strategy.items())),
        localization_accuracy=loc_acc,
        mean_detection_latency=mean_latency,
        summary_rows=_load_summary_rows(tables_dir),
        best_point=max(points, key=lambda p: p.f1) if points else None,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered)
