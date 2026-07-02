import json

import pytest

from auditcurve.models.cost import CostRecord
from auditcurve.models.mutation import ErrorType, MutatedTrajectory, Mutation, Severity
from auditcurve.models.trajectory import Trajectory
from auditcurve.models.verdict import MonitorVerdict
from auditcurve.orchestration.persistence import write_jsonl
from auditcurve.report.generator import EXPECTED_PLOTS, generate_report


def _cost():
    return CostRecord(
        model="claude-haiku-4-5",
        input_tokens=10,
        output_tokens=5,
        cost_usd=0.0007,
        latency_ms=120.0,
        timestamp="t",
    )


def _build_results_dir(tmp_path):
    results_dir = tmp_path / "results"
    plots_dir = tmp_path / "plots"
    tables_dir = tmp_path / "tables"
    results_dir.mkdir()
    plots_dir.mkdir()
    tables_dir.mkdir()

    traj = Trajectory(
        trajectory_id="traj-1",
        task_id="refunds_001_large_amount",
        steps=[],
        final_summary="done",
        ground_truth_correct=True,
        cost_record=_cost(),
    )
    write_jsonl(results_dir / "trajectories.jsonl", [traj])

    mutation = Mutation(
        mutation_id="mut-1",
        error_type=ErrorType.OMISSION,
        severity=Severity.BLATANT,
        target_step_index=1,
        description="d",
        original_trajectory_id="traj-1",
    )
    unit = MutatedTrajectory(trajectory=traj, mutation=mutation, is_mutated=True)
    write_jsonl(results_dir / "mutations.jsonl", [unit])

    verdict = MonitorVerdict(
        verdict_id="v-1",
        strategy_name="full_review",
        trajectory_id="traj-1",
        flagged=True,
        confidence=0.9,
        cost_record=_cost(),
        localized_step_index=1,
    )
    write_jsonl(results_dir / "verdicts.jsonl", [verdict])

    (results_dir / "metadata.json").write_text(
        json.dumps(
            {
                "date_run": "2026-06-24T00:00:00Z",
                "git_commit": "abc123",
                "total_api_calls": 2,
                "total_cost_usd": 0.0014,
                "pricing_last_updated": "2026-06-24",
                "model_versions": {"untrusted": "claude-sonnet-5", "trusted": "claude-haiku-4-5"},
            }
        )
    )

    for name in EXPECTED_PLOTS:
        (plots_dir / name).write_bytes(b"")

    (tables_dir / "summary_metrics.csv").write_text(
        "strategy,budget,n,mean_cost_usd,mean_latency_ms,f1\nfull_review,,1,0.0007,120.0,1.0\n"
    )

    return results_dir, plots_dir, tables_dir


def test_generate_report_produces_expected_sections(tmp_path):
    results_dir, plots_dir, tables_dir = _build_results_dir(tmp_path)
    out_path = tmp_path / "REPORT.md"

    generate_report(results_dir, plots_dir, tables_dir, out_path)

    text = out_path.read_text()
    for heading in (
        "## Abstract",
        "## Related Work",
        "## Methodology",
        "## Results",
        "## Discussion",
        "## Future Work",
        "## References",
    ):
        assert heading in text

    # a real computed number, not a placeholder string
    assert "full_review" in text
    assert "0.0007" in text or "$0.000700" in text


def test_generate_report_raises_when_plots_missing(tmp_path):
    results_dir, plots_dir, tables_dir = _build_results_dir(tmp_path)
    (plots_dir / "pareto_cost_vs_f1.png").unlink()

    with pytest.raises(FileNotFoundError):
        generate_report(results_dir, plots_dir, tables_dir, tmp_path / "REPORT.md")
