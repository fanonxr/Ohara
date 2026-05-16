# Ohara

Ohara is an AI-powered repository intelligence and deep review platform designed for Codex workflows.

V1 implements `ohara:review`: a repository scanner, markdown context builder, review template system, ChatGPT browser automation boundary, strict JSON parser, and filesystem review store.

Ohara does **not** use the OpenAI API. Its automation layer is designed to reuse authenticated ChatGPT browser sessions and ChatGPT Pro reasoning models through Playwright.

## Install

```bash
uv sync
```

Install Playwright browsers when you want live ChatGPT automation:

```bash
uv run playwright install chromium
```

## CLI

Portable package entrypoints:

```bash
uv run ohara review run --template architecture-review --repo .
uv run ohara-review run --template security-audit --repo .
uv run ohara-review run --template startup-readiness --repo . --dry-run
```

The repository also includes a local wrapper for the requested skill-style command:

```bash
./ohara:review run --template architecture-review --repo . --dry-run
```

Python packaging does not allow `:` inside console-script executable names, so the wrapper delegates to the local virtualenv `ohara-review` entrypoint when available.

## V1 Templates

- `architecture-review` - architecture boundaries, maintainability, testability, and evolution risk
- `security-audit` - credentials, dependency risks, authorization boundaries, and hardening gaps
- `startup-readiness` - operational maturity, velocity blockers, quick wins, and production readiness

## Output

Each run creates a directory under `.ohara/reviews` or the configured output directory:

```text
context.md
metadata.json
logs.txt
raw-response.md      # browser-backed runs
review.json          # validated strict JSON
```

The JSON is validated by Pydantic and shaped for Codex workflows: critical issues, technical debt, security risks, scalability issues, architecture feedback, implementation plans, quick wins, Codex actions, and recommended execution order.

## Development

```bash
uv run python -m pytest
uv run ruff check .
uv run python -m ohara --help
```

See `docs/architecture.md`, `docs/execution-flow.md`, `docs/templates.md`, `docs/extensions.md`, and `docs/configuration.md`.
