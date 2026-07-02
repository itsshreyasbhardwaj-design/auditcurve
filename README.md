# AuditCurve

**What does it actually cost, in real dollars and real milliseconds, to catch a Claude agent's mistakes with a cheaper model watching over its shoulder?**

AuditCurve is a small, open, reproducible empirical study — plus the harness that produced it — measuring the real cost/latency-vs-detection-rate Pareto frontier of *trusted monitoring*: using a cheap "trusted" model (Claude Haiku 4.5) to catch errors injected into a stronger "untrusted" agent's (Claude Sonnet 5) tool-use trajectory, on realistic, policy-driven, everyday tasks — customer refunds, travel booking, expense auditing. No math olympiad problems, no code-sabotage benchmarks: just the kind of tool-calling agent most people are actually deploying.

## Why this, and why it's not a rehash

"Scalable oversight" / "AI control" — weak models overseeing strong ones — is one of the most active alignment research areas right now, with serious prior art: Redwood Research's **AI Control** framework (the trusted-monitoring protocol this project implements), **SLEIGHT-Bench**, **CoT Red-Handed**, **AgentTrust**, **FindTheFlaws**, Anthropic's own **Sabotage evaluations for frontier models**, and the NeurIPS paper **"On Scalable Oversight with Weak LLMs Judging Strong LLMs."** All of that work measures *detection accuracy*. None of it (that we could find) reports the *dollar cost and latency* of running these protocols in practice, on the kind of everyday agentic tool-use most Claude deployments actually look like.

That's the gap this project fills — extending, not replacing, the work above. `auditcurve pilot --confirm` runs the full pilot and generates `report/REPORT.md` with the full methodology, citations, and real measured results (this repository ships the harness fully built and tested; running the pilot costs real Anthropic API dollars — see the estimate below — so no run has been executed and no results are checked in yet).

## What it does

1. Runs Claude Sonnet 5 (the "untrusted" agent) against a small suite of realistic tool-use tasks, each with an explicit policy constraint and a deterministic mock backend (no real external APIs).
2. Injects one controlled, labeled error into half the resulting trajectories via a mutation-testing-style engine (tool misuse, silent numeric error, omission, fabrication, instruction violation — each at a blatant or subtle severity).
3. Runs three trusted-monitoring strategies (full single-pass review, budget-constrained spot-check, real-time streaming) with Claude Haiku 4.5 as the "trusted" monitor, wrapping every API call to record real token usage, real dollar cost, and real wall-clock latency.
4. Computes the empirical cost-vs-detection and latency-vs-detection Pareto frontiers and generates a full technical report with plots, tables, and citations.

**No fabricated numbers anywhere.** Token costs are computed from real `usage.input_tokens`/`usage.output_tokens` against a dated pricing table; the report generator only ever reads from persisted experiment results and re-runs the analysis code — it has no path to inventing a figure.

**Status:** the harness itself is complete and verified — `ruff check .`, `mypy src/`, and `pytest tests/unit/` (71 tests) all pass with zero API calls. The pilot run (`auditcurve pilot --confirm`) has not yet been executed against the real Anthropic API, so `report/REPORT.md` and `data/results/` are not yet populated in this repository. Run `auditcurve pilot --config src/auditcurve/orchestration/config/pilot.yaml --dry-run` for the current cost estimate, then `--confirm` (with your own `ANTHROPIC_API_KEY`) to produce them.

## Installation

```bash
git clone https://github.com/itsshreyasbhardwaj-design/auditcurve.git
cd auditcurve
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Quick start

```bash
# CI-safe checks — no API key needed, zero cost
ruff check .
mypy src/
pytest tests/unit/ -v

# See the cost/call estimate for the pilot config before spending anything
export ANTHROPIC_API_KEY="sk-ant-..."
python -m auditcurve.orchestration.cli pilot --config src/auditcurve/orchestration/config/pilot.yaml --dry-run

# Run the real pilot end to end (~$1-1.50, ~15-30 min, real API spend)
python -m auditcurve.orchestration.cli pilot --config src/auditcurve/orchestration/config/pilot.yaml --confirm
```

Or, once installed as a package, the `auditcurve` command is on your `PATH` directly (`auditcurve pilot --config ... --dry-run`).

Individual pipeline stages are also independently runnable — useful for re-analyzing or re-reporting without re-spending on API calls:

```bash
auditcurve generate-trajectories --config <config.yaml> --out trajectories.jsonl
auditcurve mutate --trajectories trajectories.jsonl --config <config.yaml> --out mutations.jsonl
auditcurve run-monitors --units mutations.jsonl --config <config.yaml> --out verdicts.jsonl
auditcurve analyze --results-dir <run-dir>
auditcurve report --results-dir <run-dir>
```

## Repository layout

```
src/auditcurve/
├── models/          # Task, Trajectory, Mutation, MonitorVerdict, CostRecord — the shared contract
├── tasks/           # 3 domains (refunds, travel, expenses), 8 tasks, mock backends, ground-truth evaluators
├── agent/           # the untrusted agent's tool-use loop
├── mutate/          # the 5-error-type mutation engine
├── monitor/         # the 3 trusted-monitoring strategies
├── cost/            # real token usage -> real dollars, via a dated pricing table
├── orchestration/   # CLI, experiment config, the pipeline runner
├── analysis/        # metrics, Pareto frontier computation
└── report/          # the technical-report generator (Jinja2 -> Markdown)
```

## Documentation

- [Installation](docs/installation.md)
- [Quick Start](docs/quick-start.md)
- [Architecture](docs/architecture.md) — design decisions, modeling assumptions, and honest approximations
- [FAQ](docs/faq.md)
- [Examples](docs/examples.md)
- [Roadmap](ROADMAP.md)

## Honesty framing

This project extends Redwood Research's AI Control trusted-monitoring framework, adapts TRAIL's error taxonomy for post-hoc trajectory mutation, and follows τ²-bench's realistic multi-domain task style. It does not claim to invent scalable oversight or trusted monitoring — only the specific empirical cost-economics measurement, generated as `report/REPORT.md` by running the pilot, stated with its actual limitations (small pilot N, mock tools, single model family, post-hoc rather than adversarial mutations — see the report template's Discussion section in `src/auditcurve/report/templates/report.md.jinja2`).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
