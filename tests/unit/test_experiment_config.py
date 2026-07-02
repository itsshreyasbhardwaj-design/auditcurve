from pathlib import Path

from auditcurve.models.mutation import ErrorType, Severity
from auditcurve.orchestration.config import load_experiment_config, resolve_task_ids

PILOT_CONFIG = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "auditcurve"
    / "orchestration"
    / "config"
    / "pilot.yaml"
)


def test_load_pilot_config():
    config = load_experiment_config(PILOT_CONFIG)
    assert config.untrusted_model == "claude-sonnet-5"
    assert config.trusted_model == "claude-haiku-4-5"
    assert config.trials_per_task == 3
    assert ErrorType.TOOL_MISUSE in config.mutation_error_types
    assert Severity.BLATANT in config.mutation_severities
    assert "spot_check" in config.monitor_strategies
    assert config.spot_check_budgets == [1, 2, 4]


def test_resolve_task_ids_all_expands_to_every_registered_task():
    config = load_experiment_config(PILOT_CONFIG)
    task_ids = resolve_task_ids(config)
    assert len(task_ids) == 8


def test_config_to_dict_round_trips_enum_values():
    config = load_experiment_config(PILOT_CONFIG)
    d = config.to_dict()
    assert "tool_misuse" in d["mutation_error_types"]
    assert "blatant" in d["mutation_severities"]
