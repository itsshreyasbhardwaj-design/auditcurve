# Contributing to AuditCurve

## Development setup

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Workflow

```bash
ruff check .              # lint
ruff format .             # format
mypy src/                 # type check
pytest tests/unit/ -v     # unit tests — zero API cost, zero API key required
```

Integration tests under `tests/integration/` call the real Anthropic API and are skipped
automatically unless `ANTHROPIC_API_KEY` is set. They are not run in CI. Run them locally
only if you want to spend a few cents verifying live behavior:

```bash
pytest tests/integration/ -v
```

## Adding a new mock task domain

1. Create `src/auditcurve/tasks/<domain>/` with `schemas.py`, `backend.py`, `policy.py`,
   `evaluator.py`, `tasks.py` following the pattern in `tasks/refunds/`.
2. Register your domain's dispatch function in `src/auditcurve/agent/tool_dispatch.py`.
3. Import your domain's `tasks` module from `src/auditcurve/tasks/registry.py`'s
   `_load_all_domains()`.
4. Add unit tests under `tests/unit/test_task_evaluators.py` covering a correct and a
   policy-violating trajectory for each new task.

## Adding a new mutation error type

Add a module under `src/auditcurve/mutate/` exposing an `apply(trajectory, severity, rng,
dispatch, initial_state) -> tuple[Trajectory, str, int]` function, register it in
`_MUTATORS` in `mutate/engine.py`, and add it to `applicable_error_types()` if it has
preconditions (like `omission`/`instruction_violation` requiring a policy-required step).

## Pull requests

- Keep unit tests passing and add tests for new behavior.
- Don't commit real API keys or `data/results/` runs made with a personal key unless
  they're a deliberate, disclosed contribution to the checked-in pilot results.
- Run `ruff format .` before committing.
