# Quick Start

## 1. Verify everything works offline first (zero cost)

```bash
ruff check . && mypy src/ && pytest tests/unit/ -v
```

## 2. See what a pilot run would cost before spending anything

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
auditcurve pilot --config src/auditcurve/orchestration/config/pilot.yaml --dry-run
```

This prints an estimated task/trajectory count, call count, and dollar cost. It makes
**zero** API calls.

## 3. Run the real pilot

```bash
auditcurve pilot --config src/auditcurve/orchestration/config/pilot.yaml --confirm
```

This runs the full pipeline (generate trajectories → mutate → run monitors → analyze →
report) and writes:

- `data/results/pilot-<date>/` — raw JSONL results, the exact config snapshot, and
  `metadata.json` (git commit, model versions, total spend).
- `report/REPORT.md` — the generated technical report.
- `report/plots/*.png`, `report/tables/summary_metrics.csv` — the underlying figures/data.

## 4. Re-analyze or re-report without spending again

Every stage is independently re-runnable against already-persisted results:

```bash
auditcurve analyze --results-dir data/results/pilot-<date>
auditcurve report --results-dir data/results/pilot-<date>
```
