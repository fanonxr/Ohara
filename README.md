# Ohara

Ohara is an AI-powered repository intelligence and deep review platform designed for Codex workflows.

V1 implements `ohara:review`: a repository scanner, semantic markdown context builder,
review template system, ChatGPT browser automation boundary, strict JSON parser, and
filesystem review store.

Ohara does **not** use the OpenAI API. Its automation layer is designed to reuse authenticated ChatGPT browser sessions and ChatGPT Pro reasoning models through Microsoft `@playwright/cli`.

## Install

```bash
uv sync
```

Install Playwright CLI when you want live ChatGPT automation:

```bash
npm install -g @playwright/cli@latest
playwright-cli --help
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

## Agent Skill Setup

Ohara includes a reusable skill source at `skills/ohara-review/SKILL.md`. Keep that directory as the source of truth and symlink it into Claude/Codex skill roots:

```bash
skills/ohara-review/scripts/link-skill.sh
```

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
parse-error.txt      # browser-backed runs where JSON extraction/validation failed
```

The JSON is validated by Pydantic and shaped for Codex workflows: critical issues, technical debt, security risks, scalability issues, architecture feedback, implementation plans, quick wins, Codex actions, and recommended execution order.
Each finding includes evidence, confidence, and source paths so follow-up work can stay
grounded in the repository context.

## Context Quality

Ohara context starts with a repository briefing and guidance summary before file inventory.
It summarizes product purpose, monorepo shape, runtime components, local workflow, CI
signals, shipped versus scaffolded areas, and known tradeoffs. It also compresses
`AGENTS.md`, `CLAUDE.md`, `README.md`, architecture docs, and local specs instead of
dumping them verbatim.

The scanner detects common polyglot repo layouts, including Rust/Cargo, Axum/sqlx/Tokio,
Flutter/Dart, Next.js/React/Tailwind, Terraform, Docker Compose, and GitHub Actions.
Default excludes remove local agent/tool folders, dependency folders, build outputs,
generated Dart files, `.sqlx` metadata for non-security reviews, and platform assets.

## Browser Automation

Ohara uses `playwright-cli`, not Playwright MCP and not the Python Playwright API. The default browser session is:

```bash
playwright-cli -s=ohara-chatgpt open https://chatgpt.com/ --persistent --profile=.ohara/playwright-cli-profile --headed
```

Sign into ChatGPT once in that headed browser. Later browser-backed runs reuse the named CLI session and persistent profile.

## Development

```bash
uv run python -m pytest
uv run ruff check .
uv run python -m ohara --help
```

See `docs/architecture.md`, `docs/execution-flow.md`, `docs/templates.md`, `docs/extensions.md`, and `docs/configuration.md`.
