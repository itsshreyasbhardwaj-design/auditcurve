# Examples

## Running the full pipeline at once (`pilot`)

```bash
auditcurve pilot --config src/auditcurve/orchestration/config/pilot.yaml --dry-run
auditcurve pilot --config src/auditcurve/orchestration/config/pilot.yaml --confirm
```

`pilot` runs `generate-trajectories → mutate → run-monitors → analyze → report` end to end
and writes everything under `data/results/<run_id>/` plus `report/`. This is the command
to run to produce `report/REPORT.md` — as of this writing no pilot run has been executed
against the real API yet, so `report/` and `data/results/` are empty in this repository
(see the README's Status note).

## Running each stage independently

Each stage reads its input from JSONL and writes its output to JSONL, so any stage can be
re-run on its own without re-spending on the stages before it — useful when iterating on
analysis or the report template against an already-paid-for set of trajectories/verdicts.

```bash
# 1. Generate trajectories (spends money: runs the untrusted agent against every task/trial)
auditcurve generate-trajectories \
  --config src/auditcurve/orchestration/config/pilot.yaml \
  --out data/results/manual-run/trajectories.jsonl

# 2. Apply mutations (free — pure Python, no API calls)
auditcurve mutate \
  --trajectories data/results/manual-run/trajectories.jsonl \
  --config src/auditcurve/orchestration/config/pilot.yaml \
  --out data/results/manual-run/mutations.jsonl

# 3. Run the trusted monitors against each evaluation unit (spends money)
auditcurve run-monitors \
  --units data/results/manual-run/mutations.jsonl \
  --config src/auditcurve/orchestration/config/pilot.yaml \
  --out data/results/manual-run/verdicts.jsonl

# 4. Compute metrics/Pareto frontier and render plots + summary_metrics.csv (free)
auditcurve analyze --results-dir data/results/manual-run

# 5. Render the technical report from the persisted results (free)
auditcurve report --results-dir data/results/manual-run --out report/REPORT.md
```

## Re-analyzing or re-reporting without spending again

Because `trajectories.jsonl` and `verdicts.jsonl` are already on disk, you can rerun just
the free stages — e.g. after changing a metric definition or the report template:

```bash
auditcurve analyze --results-dir data/results/pilot-<date>
auditcurve report --results-dir data/results/pilot-<date>
```

## Interpreting the Pareto frontier in the report

`report/tables/summary_metrics.csv` has one row per `(strategy, budget)` pair with mean
cost (USD), mean latency (ms), and detection F1. `analysis/pareto.py` marks a point as
**on the frontier** if no other point beats it on both cost and F1 simultaneously (and
separately for latency and F1) — those are the strategies worth considering; a dominated
point is strictly worse on both axes than some cheaper-or-faster alternative and can be
ruled out regardless of budget. `report/plots/cost_vs_f1_pareto.png` and
`latency_vs_f1_pareto.png` draw the same frontier visually, with dominated points shown
but not connected by the frontier line.

## Adding a new task domain

See `CONTRIBUTING.md` § Adding a new mock task domain for the full walkthrough (schemas,
mock backend, policy constraint, evaluator, task registration).
