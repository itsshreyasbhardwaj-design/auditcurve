# Installation

Requires Python 3.11+.

```bash
git clone https://github.com/itsshreyasbhardwaj-design/auditcurve.git
cd auditcurve
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

No API key is required to install, lint, type-check, or run the unit test suite — those
are fully offline and free. An `ANTHROPIC_API_KEY` is only needed for:

- `auditcurve pilot --confirm` (or any of the individual `generate-trajectories` /
  `run-monitors` subcommands) — this spends real money.
- `pytest tests/integration/` — the gated, opt-in live-API test suite.

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Verify the install:

```bash
pytest tests/unit/ -v
```
