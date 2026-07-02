# Security Policy

AuditCurve is a research/portfolio project, not a production service. Still, a few things
are worth knowing:

- **API keys.** The project reads `ANTHROPIC_API_KEY` from your environment; it is never
  logged, written to disk, or included in any persisted result file. If you find a code
  path that does log or persist a key, please report it (see below) — that would be a bug.
- **MCP server / vault credentials are not applicable here** — this project only talks to
  the Anthropic Messages API directly, with deterministic in-memory mock tool backends. No
  real external systems are ever called.
- **Mock backends are not sandboxed execution.** They are plain Python functions operating
  on an in-memory dict; they do not execute model-generated code.

## Reporting a vulnerability

Please open a private security advisory on GitHub, or email the address listed on the
maintainer's GitHub profile, rather than filing a public issue for anything sensitive.
