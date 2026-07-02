# Architecture

## The core insight, as code

`MutatedTrajectory` (in `models/mutation.py`) is the *only* place ground-truth labels live.
Monitor strategy functions (`monitor/*.py`) take a bare `Trajectory`, never a
`MutatedTrajectory` — enforced by function signatures, not just convention. This is what
makes the experiment honest: a monitor cannot accidentally see whether the trajectory it's
reviewing is mutated.

## Data flow

```
Task (tasks/<domain>/tasks.py)
  → agent/runner.py (Claude Sonnet 5 + real mock backend) → Trajectory
  → task.evaluator (replay-and-check against the real backend) → ground_truth_correct
  → mutate/engine.py (~50% of correct trajectories get one labeled error) → MutatedTrajectory
  → monitor/{full_review,spot_check,streaming}.py (Claude Haiku 4.5) → MonitorVerdict
  → analysis/{metrics,pareto}.py → StrategyPoint (cost, latency, F1) → Pareto frontier
  → report/generator.py (Jinja2) → REPORT.md
```

Every stage persists to JSONL under `data/results/<run_id>/` and every later stage reads
only from disk — nothing is passed in memory across CLI invocations, which is what makes
`auditcurve analyze` / `auditcurve report` re-runnable without re-spending on API calls.

## Modeling assumptions and approximations, stated explicitly

- **Token cost is estimated using real `usage.input_tokens`/`usage.output_tokens`**, not
  approximated — this project never estimates token counts, only converts real counts to
  dollars via the dated pricing table in `cost/pricing_config.yaml`.
- **The mutation engine edits a *known-correct* trajectory post-hoc.** It does not simulate
  a genuinely adversarial untrusted agent trying to evade detection. This is a deliberate
  scoping choice (see the report's Limitations section) — it isolates "can the monitor catch
  a labeled error" from "can the monitor resist an agent actively trying to fool it," which
  is a different (and already well-studied, e.g. SLEIGHT-Bench) question.
- **Commands' mock backends are deterministic Python functions**, not real external APIs.
  This keeps the whole pipeline offline-and-free except for the two real model call sites
  (the untrusted agent and the trusted monitor).
- **`spot_check`'s two-phase design (triage call, then verdict call) is deliberate** — a
  single-call version where the experimenter hands the monitor "here are steps 2 and 4"
  would beg the question of who chose those steps. Making step-selection itself a costed
  monitor decision is what makes this strategy's cost profile meaningfully different from
  "just inspect a fixed percentage of steps."
- **`streaming`'s incremental calls simulate a real-time hook** (like Claude Code's
  `PreToolUse`) by replaying the trajectory step-by-step and calling the monitor with only
  the prefix seen so far — this is a genuine simulation of what a production real-time
  monitor would see, not an approximation of it.

## Why Python, not TypeScript

This project's sibling ([claude-code-labs](https://github.com/itsshreyasbhardwaj-design/claude-code-labs))
is a TypeScript CLI. AuditCurve is Python because its audience (ML/AI-safety researchers) and
its dependencies (the Anthropic Python SDK, matplotlib for static plots, Jinja2 for the
report) are more natural in Python, and because the research-tooling convention in this
specific field (Inspect, control-arena-style harnesses) leans Python.
