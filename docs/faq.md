# FAQ

**Does this cost money to run?**
Installing, linting, type-checking, and running the unit test suite are free and fully
offline. Only `auditcurve pilot --confirm` (or the individual trajectory-generation /
monitor-running subcommands, or `pytest tests/integration/`) call the real Anthropic API
and spend real money — the pilot config is sized to cost roughly $1-1.50.

**Is this claiming to be novel AI safety research?**
No — see the Honesty Framing section of the README and the Related Work section of the
report template (`src/auditcurve/report/templates/report.md.jinja2`). This project extends
existing trusted-monitoring work (Redwood Research's AI Control framework, TRAIL's error
taxonomy, τ²-bench's task style) with one specific, apparently-unreported empirical
measurement: real dollar cost and latency plotted against detection rate, on everyday
tool-use tasks.

**Why only 3 monitor strategies?**
Full review, budget-constrained spot-check, and streaming were chosen because they have
genuinely different cost *shapes* (one big call vs. many small calls vs. a two-phase
triage-then-verdict call), which is exactly what a cost-economics study needs to compare.
See `ROADMAP.md` for a planned fourth ("untrusted monitoring") strategy.

**Can I add my own task domain?**
Yes — see `CONTRIBUTING.md` § Adding a new mock task domain.

**Why mock tool backends instead of real external APIs?**
Real external APIs would make the pilot non-reproducible (rate limits, changing data,
network flakiness) and non-free. The mock backends are deterministic, so the exact same
config always produces comparable trajectories, and the whole pipeline stays fully offline
except for the two real model call sites (the untrusted agent and the trusted monitor).

**Where are the actual results?**
`report/REPORT.md`, generated from the raw JSONL under `data/results/<run_id>/`, once
someone runs `auditcurve pilot --confirm` with their own `ANTHROPIC_API_KEY` — the harness
is fully built and tested, but that paid run hasn't been executed yet, so neither file
exists in this repository as of this writing. See the README's Status note.
