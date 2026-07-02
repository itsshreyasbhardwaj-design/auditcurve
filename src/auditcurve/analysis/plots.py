"""Static matplotlib PNGs + summary_metrics.csv. No interactive/plotly — everything here
is deterministic given the same persisted results."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..models.mutation import MutatedTrajectory
from ..models.trajectory import Trajectory
from ..models.verdict import MonitorVerdict
from ..orchestration.persistence import read_jsonl
from .metrics import metrics_by_group
from .pareto import StrategyPoint, aggregate_strategy_points, pareto_frontier


def load_results(
    results_dir: Path,
) -> tuple[list[Trajectory], list[MutatedTrajectory], list[MonitorVerdict]]:
    trajectories = read_jsonl(results_dir / "trajectories.jsonl", Trajectory.from_dict)
    mutations = read_jsonl(results_dir / "mutations.jsonl", MutatedTrajectory.from_dict)
    verdicts = read_jsonl(results_dir / "verdicts.jsonl", MonitorVerdict.from_dict)
    return trajectories, mutations, verdicts


def plot_pareto(
    points: list[StrategyPoint],
    frontier: list[StrategyPoint],
    cost_axis: str,
    out_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(7, 5))

    by_strategy: dict[str, list[StrategyPoint]] = {}
    for p in points:
        by_strategy.setdefault(p.strategy_name, []).append(p)

    for strategy, pts in by_strategy.items():
        xs = [p.mean_cost_usd if cost_axis == "cost" else p.mean_latency_ms for p in pts]
        ys = [p.f1 for p in pts]
        ax.scatter(xs, ys, label=strategy, s=60)

    frontier_sorted = sorted(
        frontier, key=lambda p: p.mean_cost_usd if cost_axis == "cost" else p.mean_latency_ms
    )
    fx = [p.mean_cost_usd if cost_axis == "cost" else p.mean_latency_ms for p in frontier_sorted]
    fy = [p.f1 for p in frontier_sorted]
    ax.plot(fx, fy, "k--", label="Pareto frontier", linewidth=1.5)

    ax.set_xlabel("Mean cost (USD, est.)" if cost_axis == "cost" else "Mean latency (ms)")
    ax.set_ylabel("F1 (detection)")
    ax.set_title("Cost vs. Detection F1" if cost_axis == "cost" else "Latency vs. Detection F1")
    ax.legend()
    fig.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_f1_by_category_severity(
    verdicts: list[MonitorVerdict], mutations: list[MutatedTrajectory], out_path: Path
) -> None:
    by_error = metrics_by_group(verdicts, mutations, "error_type")
    by_severity = metrics_by_group(verdicts, mutations, "severity")

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))

    labels1 = sorted(by_error.keys())
    axes[0].bar(labels1, [by_error[k][2] for k in labels1])
    axes[0].set_title("F1 by error type")
    axes[0].set_ylabel("F1")
    axes[0].tick_params(axis="x", rotation=30)

    labels2 = sorted(by_severity.keys())
    axes[1].bar(labels2, [by_severity[k][2] for k in labels2])
    axes[1].set_title("F1 by severity")

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def write_summary_csv(
    verdicts: list[MonitorVerdict], mutations: list[MutatedTrajectory], out_path: Path
) -> None:
    points = aggregate_strategy_points(verdicts, mutations)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["strategy", "budget", "n", "mean_cost_usd", "mean_latency_ms", "f1"])
        for p in sorted(points, key=lambda p: (p.strategy_name, p.budget or 0)):
            writer.writerow(
                [
                    p.strategy_name,
                    p.budget,
                    p.n,
                    round(p.mean_cost_usd, 6),
                    round(p.mean_latency_ms, 1),
                    round(p.f1, 4),
                ]
            )


def generate_all_plots_and_tables(results_dir: Path, plots_dir: Path, tables_dir: Path) -> None:
    _trajectories, mutations, verdicts = load_results(results_dir)
    points = aggregate_strategy_points(verdicts, mutations)

    plot_pareto(
        points, pareto_frontier(points, "cost"), "cost", plots_dir / "pareto_cost_vs_f1.png"
    )
    plot_pareto(
        points,
        pareto_frontier(points, "latency"),
        "latency",
        plots_dir / "pareto_latency_vs_f1.png",
    )
    plot_f1_by_category_severity(verdicts, mutations, plots_dir / "f1_by_category_severity.png")
    write_summary_csv(verdicts, mutations, tables_dir / "summary_metrics.csv")
