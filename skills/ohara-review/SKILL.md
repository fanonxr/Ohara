---
name: ohara-review
description: Use when Codex or Claude needs repository intelligence, deep code review, architecture review, security audit, startup-readiness review, or strict JSON review output using the local Ohara project.
---

# Ohara Review

## Purpose

Use Ohara to scan repositories, build compact markdown context packages, submit review prompts through ChatGPT browser automation, parse strict JSON, and save review artifacts for Codex or Claude workflows.

Ohara does not use the OpenAI API. Browser-backed runs use the Microsoft `@playwright/cli` command, not Playwright MCP and not the Python Playwright API.

## Setup

This skill is intended to live in the Ohara repository and be symlinked into agent skill roots.

From the Ohara repo root:

```bash
skills/ohara-review/scripts/link-skill.sh
uv sync
npm install -g @playwright/cli@latest
playwright-cli --help
```

Manual symlink commands:

```bash
mkdir -p "$HOME/.claude/skills" "$HOME/.codex/skills"
ln -sfn "$PWD/skills/ohara-review" "$HOME/.claude/skills/ohara-review"
ln -sfn "$PWD/skills/ohara-review" "$HOME/.codex/skills/ohara-review"
```

If your Codex install uses `~/.agents/skills`, link there as well:

```bash
mkdir -p "$HOME/.agents/skills"
ln -sfn "$PWD/skills/ohara-review" "$HOME/.agents/skills/ohara-review"
```

## Quick Commands

Generate context only:

```bash
./ohara:review run --template architecture-review --repo . --dry-run
```

Run through the portable package entrypoint:

```bash
uv run ohara-review run --template security-audit --repo .
uv run ohara review run --template startup-readiness --repo .
```

Install or verify Playwright CLI support for live ChatGPT automation:

```bash
npm install -g @playwright/cli@latest
playwright-cli --help
```

If global install is not available, try a local install path and use that command consistently:

```bash
npx playwright-cli --help
```

## Review Templates

- `architecture-review`: module boundaries, architecture risks, maintainability, execution order
- `security-audit`: credential exposure, auth boundaries, dependency/configuration risks
- `startup-readiness`: production readiness, velocity blockers, operational gaps, quick wins

## Agent Workflow

1. Locate the Ohara repo root. If this skill is symlinked, resolve the real path of this skill directory and go two directories up.
2. Run a dry run first to inspect context quality.
3. For browser-backed runs, ensure the ChatGPT browser profile is authenticated using a persistent named CLI session.
4. Use the generated `review.json` as machine-readable input for implementation, planning, or refactoring.
5. Do not call the OpenAI API for this workflow.
6. Do not use Playwright MCP for this workflow.

## Playwright CLI Session

Ohara defaults to:

```bash
playwright-cli -s=ohara-chatgpt open https://chatgpt.com/ --persistent --profile=.ohara/playwright-cli-profile --headed
```

Sign into ChatGPT in that browser once. Later `ohara:review` browser-backed runs reuse the same session/profile.

Useful CLI commands:

```bash
playwright-cli list
playwright-cli show
playwright-cli -s=ohara-chatgpt close
```

## Output Locations

Default review artifacts are written under `.ohara/reviews/`:

```text
context.md
metadata.json
logs.txt
raw-response.md
review.json
```

## Validation

Before relying on changes to Ohara itself:

```bash
uv run python -m pytest
uv run ruff check .
```
