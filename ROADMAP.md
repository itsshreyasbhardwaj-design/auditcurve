# Roadmap

## Shipped (v1 harness)

- 3 task domains (refunds, travel, expenses), 8 tasks, deterministic mock backends.
- 5-error-type mutation engine (tool misuse, silent numeric error, omission, fabrication,
  instruction violation), each at blatant/subtle severity.
- 3 trusted-monitoring strategies (full review, budget-constrained spot-check, streaming
  step-wise) with real cost/latency measurement.
- Cost/latency Pareto frontier analysis + a report generator that turns a completed pilot
  run into a full technical report. `ruff check .` / `mypy src/` / `pytest tests/unit/` all
  pass with zero API calls; the paid pilot run itself (`auditcurve pilot --confirm`) has not
  yet been executed, so no results are checked into this repository yet — see the README's
  Status note.

## Near-term

- **Run and check in the v1 pilot results.** Everything needed to produce `report/REPORT.md`
  and `data/results/` is built and tested; it just needs someone with Anthropic API budget
  (~$1-1.50) to run `auditcurve pilot --confirm`.
- **Larger-N runs with confidence intervals.** The v1 pilot is deliberately small
  (~$1-1.50, single pass per configuration). A larger sweep with repeated trials would let
  the report state statistical significance rather than point estimates.
- **A `--live` MCP introspection mode** — out of scope for v1 entirely; this project doesn't
  touch MCP at all today, but a natural extension would measure tool-schema-heavy agentic
  setups specifically.
- **Adversarial, evasion-aware mutations** — closer to SLEIGHT-Bench's framing: instead of
  post-hoc editing a known-correct trajectory, have the untrusted agent itself try to
  produce a subtly-wrong-but-persuasive trajectory, and measure whether monitors catch an
  agent that's actively trying to evade detection (not just a mechanically injected error).
- **Cross-provider trusted models** — measure whether a non-Anthropic cheap model changes
  the cost/detection trade-off.

## Longer-term / speculative

- A fourth monitor strategy: "untrusted monitoring" (per Redwood's AI Control paper) — using
  a same-capability model with scratchpad reasoning as the monitor, for comparison against
  the trusted-monitoring strategies here.
- A small task-suite generator so new domains can be scaffolded faster than hand-writing
  `schemas.py`/`backend.py`/`policy.py`/`evaluator.py`/`tasks.py` each time.
- Packaging the mutation engine as a standalone library usable against other agent
  trajectory formats (e.g. LangChain, OpenAI function-calling traces), decoupled from
  AuditCurve's specific task suite.
