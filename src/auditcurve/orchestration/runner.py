"""Orchestrates the experiment pipeline: generate trajectories -> mutate -> run monitors.
Each stage is a pure function over persisted JSONL, so any stage can be re-run
independently without re-spending on the ones before it."""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from ..agent.runner import run_agent
from ..cost.pricing import PricingTable, load_pricing_table
from ..models.cost import CostRecord
from ..models.mutation import MutatedTrajectory
from ..models.trajectory import Trajectory
from ..models.verdict import MonitorVerdict
from ..monitor import STRATEGIES
from ..mutate.engine import applicable_error_types, apply_mutation, make_control
from ..tasks.registry import get_task
from .config import ExperimentConfig, resolve_task_ids


def generate_trajectories(
    client: Any, config: ExperimentConfig, pricing_table: PricingTable
) -> list[Trajectory]:
    task_ids = resolve_task_ids(config)
    trajectories: list[Trajectory] = []
    for task_id in task_ids:
        task = get_task(task_id)
        for _trial in range(config.trials_per_task):
            traj = run_agent(client, task, config.untrusted_model, pricing_table)
            result = task.evaluator(traj, task.initial_state)
            traj = dataclasses.replace(traj, ground_truth_correct=result.correct)
            trajectories.append(traj)
    return trajectories


def build_evaluation_units(
    trajectories: list[Trajectory], config: ExperimentConfig
) -> list[MutatedTrajectory]:
    import random

    rng = random.Random(config.random_seed)
    correct = [t for t in trajectories if t.ground_truth_correct]
    skipped = len(trajectories) - len(correct)
    if skipped:
        print(
            f"auditcurve: excluding {skipped} trajectory(ies) where the untrusted agent "
            "itself did not solve the task correctly (mutation testing needs a known-correct "
            "baseline)",
            file=sys.stderr,
        )

    units: list[MutatedTrajectory] = []
    for traj in correct:
        task = get_task(traj.task_id)
        if rng.random() >= config.mutated_fraction:
            units.append(make_control(traj))
            continue

        applicable = [e for e in applicable_error_types(traj) if e in config.mutation_error_types]
        if not applicable:
            units.append(make_control(traj))
            continue

        error_type = rng.choice(applicable)
        severity = rng.choice(config.mutation_severities)
        try:
            units.append(apply_mutation(traj, task, error_type, severity, rng))
        except ValueError:
            units.append(make_control(traj))

    return units


def run_monitors(
    client: Any,
    units: list[MutatedTrajectory],
    config: ExperimentConfig,
    pricing_table: PricingTable,
) -> list[MonitorVerdict]:
    verdicts: list[MonitorVerdict] = []
    for unit in units:
        traj = unit.trajectory
        task = get_task(traj.task_id)
        for strategy_name in config.monitor_strategies:
            strategy_fn = STRATEGIES[strategy_name]
            if strategy_name == "spot_check":
                for budget in config.spot_check_budgets:
                    verdicts.append(
                        strategy_fn(
                            client, traj, task, config.trusted_model, pricing_table, budget=budget
                        )
                    )
            else:
                verdicts.append(
                    strategy_fn(client, traj, task, config.trusted_model, pricing_table)
                )
    return verdicts


def estimate_pilot(config: ExperimentConfig, pricing_table: PricingTable | None = None) -> dict:
    """A rough, clearly-labeled pre-flight estimate — NOT a guarantee. Calibrated to the
    shapes observed while designing the pilot config (see docs/architecture.md)."""
    pricing_table = pricing_table or load_pricing_table()
    task_ids = resolve_task_ids(config)
    num_tasks = len(task_ids)
    num_trajectories = num_tasks * config.trials_per_task

    avg_agent_calls_per_trajectory = 2.5
    avg_agent_input_tokens = 2000
    avg_agent_output_tokens = 400
    num_agent_calls = round(num_trajectories * avg_agent_calls_per_trajectory)

    strategy_call_counts = {
        "full_review": 1,
        "spot_check": 2 * max(len(config.spot_check_budgets), 1),
        "streaming": 6,  # ~5 steps + 1 possible final check, upper bound
    }
    calls_per_unit = sum(strategy_call_counts.get(s, 0) for s in config.monitor_strategies)
    num_monitor_calls = num_trajectories * calls_per_unit

    avg_monitor_input_tokens = 1200
    avg_monitor_output_tokens = 120

    agent_pricing = pricing_table.get(config.untrusted_model)
    monitor_pricing = pricing_table.get(config.trusted_model)
    agent_in_rate, agent_out_rate = agent_pricing.effective_rates()
    monitor_in_rate, monitor_out_rate = monitor_pricing.effective_rates()

    agent_cost = num_agent_calls * (
        (avg_agent_input_tokens / 1_000_000) * agent_in_rate
        + (avg_agent_output_tokens / 1_000_000) * agent_out_rate
    )
    monitor_cost = num_monitor_calls * (
        (avg_monitor_input_tokens / 1_000_000) * monitor_in_rate
        + (avg_monitor_output_tokens / 1_000_000) * monitor_out_rate
    )

    return {
        "num_tasks": num_tasks,
        "num_trajectories": num_trajectories,
        "estimated_agent_calls": num_agent_calls,
        "estimated_monitor_calls": num_monitor_calls,
        "estimated_total_calls": num_agent_calls + num_monitor_calls,
        "estimated_cost_usd": round(agent_cost + monitor_cost, 2),
    }


def write_metadata(
    run_dir: Path,
    config: ExperimentConfig,
    all_costs: list[CostRecord],
    pricing_table: PricingTable,
) -> None:
    try:
        repo_root = Path(__file__).resolve().parents[3]
        git_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        git_commit = None

    try:
        import anthropic

        sdk_version = getattr(anthropic, "__version__", "unknown")
    except Exception:
        sdk_version = "unknown"

    metadata = {
        "date_run": dt.datetime.now(dt.UTC).isoformat(),
        "git_commit": git_commit,
        "anthropic_sdk_version": sdk_version,
        "model_versions": {"untrusted": config.untrusted_model, "trusted": config.trusted_model},
        "pricing_last_updated": pricing_table.last_updated,
        "total_api_calls": len(all_costs),
        "total_cost_usd": round(sum(c.cost_usd for c in all_costs), 4),
    }
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
