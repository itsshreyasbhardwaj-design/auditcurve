"""auditcurve CLI. Each subcommand is independently invocable so a partial re-run (e.g.
re-analyze without re-spending on API calls) is cheap. `pilot` runs the full pipeline."""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import click

RESULTS_ROOT = Path("data/results")
REPORT_ROOT = Path("report")


def _client():
    import anthropic

    return anthropic.Anthropic()


def _run_dir(run_id: str) -> Path:
    return RESULTS_ROOT / run_id


@click.group()
def cli() -> None:
    """auditcurve: the real dollar-cost and latency Pareto frontier of trusted monitoring."""


@cli.command("generate-trajectories")
@click.option(
    "--config", "config_path", required=True, type=click.Path(exists=True, path_type=Path)
)
@click.option("--out", "out_path", required=True, type=click.Path(path_type=Path))
def generate_trajectories_cmd(config_path: Path, out_path: Path) -> None:
    from ..cost.pricing import load_pricing_table
    from .config import load_experiment_config
    from .persistence import write_jsonl
    from .runner import generate_trajectories

    config = load_experiment_config(config_path)
    pricing_table = load_pricing_table()
    client = _client()

    trajectories = generate_trajectories(client, config, pricing_table)
    write_jsonl(out_path, trajectories)
    click.echo(f"Wrote {len(trajectories)} trajectories to {out_path}")


@cli.command("mutate")
@click.option(
    "--trajectories",
    "trajectories_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    "--config", "config_path", required=True, type=click.Path(exists=True, path_type=Path)
)
@click.option("--out", "out_path", required=True, type=click.Path(path_type=Path))
def mutate_cmd(trajectories_path: Path, config_path: Path, out_path: Path) -> None:
    from ..models.trajectory import Trajectory
    from .config import load_experiment_config
    from .persistence import read_jsonl, write_jsonl
    from .runner import build_evaluation_units

    config = load_experiment_config(config_path)
    trajectories = read_jsonl(trajectories_path, Trajectory.from_dict)
    units = build_evaluation_units(trajectories, config)
    write_jsonl(out_path, units)
    mutated_count = sum(1 for u in units if u.is_mutated)
    control_count = len(units) - mutated_count
    click.echo(
        f"Wrote {len(units)} evaluation units ({mutated_count} mutated, "
        f"{control_count} control) to {out_path}"
    )


@cli.command("run-monitors")
@click.option("--units", "units_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option(
    "--config", "config_path", required=True, type=click.Path(exists=True, path_type=Path)
)
@click.option("--out", "out_path", required=True, type=click.Path(path_type=Path))
def run_monitors_cmd(units_path: Path, config_path: Path, out_path: Path) -> None:
    from ..cost.pricing import load_pricing_table
    from ..models.mutation import MutatedTrajectory
    from .config import load_experiment_config
    from .persistence import read_jsonl, write_jsonl
    from .runner import run_monitors

    config = load_experiment_config(config_path)
    pricing_table = load_pricing_table()
    client = _client()

    units = read_jsonl(units_path, MutatedTrajectory.from_dict)
    verdicts = run_monitors(client, units, config, pricing_table)
    write_jsonl(out_path, verdicts)
    click.echo(f"Wrote {len(verdicts)} monitor verdicts to {out_path}")


@cli.command("analyze")
@click.option("--results-dir", required=True, type=click.Path(exists=True, path_type=Path))
def analyze_cmd(results_dir: Path) -> None:
    from ..analysis.plots import generate_all_plots_and_tables

    generate_all_plots_and_tables(results_dir, REPORT_ROOT / "plots", REPORT_ROOT / "tables")
    click.echo(f"Wrote plots to {REPORT_ROOT / 'plots'} and tables to {REPORT_ROOT / 'tables'}")


@cli.command("report")
@click.option("--results-dir", required=True, type=click.Path(exists=True, path_type=Path))
@click.option(
    "--out", "out_path", default=REPORT_ROOT / "REPORT.md", type=click.Path(path_type=Path)
)
def report_cmd(results_dir: Path, out_path: Path) -> None:
    from ..report.generator import generate_report

    generate_report(results_dir, REPORT_ROOT / "plots", REPORT_ROOT / "tables", out_path)
    click.echo(f"Wrote report to {out_path}")


@cli.command("pilot")
@click.option(
    "--config", "config_path", required=True, type=click.Path(exists=True, path_type=Path)
)
@click.option(
    "--dry-run", is_flag=True, help="Print the cost/call estimate without spending anything."
)
@click.option("--confirm", is_flag=True, help="Actually run and spend real API dollars.")
def pilot_cmd(config_path: Path, dry_run: bool, confirm: bool) -> None:
    from ..cost.pricing import load_pricing_table
    from .config import load_experiment_config, write_config_snapshot
    from .persistence import write_jsonl
    from .runner import (
        build_evaluation_units,
        estimate_pilot,
        generate_trajectories,
        run_monitors,
        write_metadata,
    )

    config = load_experiment_config(config_path)
    pricing_table = load_pricing_table()

    if not dry_run and not confirm:
        click.echo(
            "Refusing to run without --dry-run or --confirm. This command spends real "
            "Anthropic API dollars — run with --dry-run first to see the estimate.",
            err=True,
        )
        sys.exit(1)

    estimate = estimate_pilot(config, pricing_table)
    click.echo(
        f"Estimate: {estimate['num_tasks']} tasks x trials -> {estimate['num_trajectories']} "
        f"trajectories, ~{estimate['estimated_agent_calls']} agent calls + "
        f"~{estimate['estimated_monitor_calls']} monitor calls "
        f"(~{estimate['estimated_total_calls']} total), ~${estimate['estimated_cost_usd']:.2f} "
        f"estimated cost. This is a rough estimate, not a guarantee."
    )

    if dry_run:
        return

    import dataclasses

    run_id = f"{config.run_id}-{dt.date.today().isoformat()}"
    config = dataclasses.replace(config, run_id=run_id)
    run_dir = _run_dir(run_id)

    write_config_snapshot(config, run_dir / "config_used.yaml")

    client = _client()

    click.echo("Generating trajectories...")
    trajectories = generate_trajectories(client, config, pricing_table)
    write_jsonl(run_dir / "trajectories.jsonl", trajectories)

    click.echo("Applying mutations...")
    units = build_evaluation_units(trajectories, config)
    write_jsonl(run_dir / "mutations.jsonl", units)

    click.echo("Running monitors...")
    verdicts = run_monitors(client, units, config, pricing_table)
    write_jsonl(run_dir / "verdicts.jsonl", verdicts)

    all_costs = [t.cost_record for t in trajectories if t.cost_record] + [
        v.cost_record for v in verdicts
    ]
    write_metadata(run_dir, config, all_costs, pricing_table)

    click.echo("Analyzing...")
    from ..analysis.plots import generate_all_plots_and_tables

    generate_all_plots_and_tables(run_dir, REPORT_ROOT / "plots", REPORT_ROOT / "tables")

    click.echo("Generating report...")
    from ..report.generator import generate_report

    generate_report(
        run_dir, REPORT_ROOT / "plots", REPORT_ROOT / "tables", REPORT_ROOT / "REPORT.md"
    )

    total_cost = sum(c.cost_usd for c in all_costs)
    report_path = REPORT_ROOT / "REPORT.md"
    click.echo(
        f"Done. Total spend: ${total_cost:.4f}. Results in {run_dir}, report at {report_path}"
    )


if __name__ == "__main__":
    cli()
