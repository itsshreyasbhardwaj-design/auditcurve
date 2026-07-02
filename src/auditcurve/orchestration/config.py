"""ExperimentConfig: everything one pilot run needs, loaded from a YAML file so the exact
configuration used can be snapshotted alongside the results for reproducibility."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from ..models.mutation import ErrorType, Severity


@dataclass(frozen=True)
class ExperimentConfig:
    run_id: str
    untrusted_model: str
    trusted_model: str
    tasks: list[str]
    trials_per_task: int
    mutation_error_types: list[ErrorType]
    mutation_severities: list[Severity]
    mutated_fraction: float
    monitor_strategies: list[str]
    spot_check_budgets: list[int]
    random_seed: int

    def to_dict(self) -> dict:
        d = asdict(self)
        d["mutation_error_types"] = [e.value for e in self.mutation_error_types]
        d["mutation_severities"] = [s.value for s in self.mutation_severities]
        return d


def load_experiment_config(path: Path) -> ExperimentConfig:
    raw = yaml.safe_load(Path(path).read_text())
    tasks = raw["tasks"]
    if isinstance(tasks, str):
        tasks = [tasks]

    return ExperimentConfig(
        run_id=raw["run_id"],
        untrusted_model=raw["untrusted_model"],
        trusted_model=raw["trusted_model"],
        tasks=tasks,
        trials_per_task=raw["trials_per_task"],
        mutation_error_types=[ErrorType(e) for e in raw["mutation_error_types"]],
        mutation_severities=[Severity(s) for s in raw["mutation_severities"]],
        mutated_fraction=raw["mutated_fraction"],
        monitor_strategies=raw["monitor_strategies"],
        spot_check_budgets=raw["spot_check_budgets"],
        random_seed=raw["random_seed"],
    )


def resolve_task_ids(config: ExperimentConfig) -> list[str]:
    from ..tasks.registry import all_tasks

    if config.tasks == ["all"]:
        return [t.task_id for t in all_tasks()]
    return config.tasks


def write_config_snapshot(config: ExperimentConfig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(config.to_dict(), sort_keys=False))
