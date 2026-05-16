# Ohara Review V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the V1 `ohara:review` skill as a tested, extensible Python platform scaffold.

**Architecture:** Implement an offline-testable repository intelligence core with a provider interface for ChatGPT browser automation. The CLI coordinates scanning, context generation, prompt templating, strict JSON parsing, and filesystem persistence through `ReviewRunner`.

**Tech Stack:** Python 3.12+, `uv`, Typer, Rich, Pydantic, Playwright, pytest, pathlib, asyncio.

---

### Task 1: Project Foundation

**Files:**
- Create: `pyproject.toml`
- Create: `ohara/__init__.py`
- Create: `ohara/__main__.py`
- Create: `ohara/cli/app.py`
- Create: `ohara/cli/review.py`

- [ ] Write package metadata and console scripts for `ohara` and `ohara:review`.
- [ ] Add Typer CLI shells with `run --template`, `--repo`, `--output`, `--dry-run`, and `--no-browser`.
- [ ] Verify CLI imports with `uv run python -m ohara --help`.

### Task 2: Schemas and Templates

**Files:**
- Create: `ohara/schemas/review.py`
- Create: `ohara/templates/base.py`
- Create: `ohara/templates/registry.py`

- [ ] Write failing tests for strict review schema validation and template lookup.
- [ ] Implement Pydantic models for issues, risks, implementation plans, quick wins, Codex actions, and execution order.
- [ ] Implement three V1 templates: `architecture-review`, `security-audit`, and `startup-readiness`.
- [ ] Verify tests pass.

### Task 3: Repository Intelligence

**Files:**
- Create: `ohara/context/models.py`
- Create: `ohara/context/scanner.py`
- Create: `ohara/context/builder.py`

- [ ] Write failing tests for multi-repo scanning, ignore rules, framework/dependency detection, TODO extraction, risk detection, and context markdown.
- [ ] Implement deterministic scanning with default excludes and important-file prioritization.
- [ ] Implement markdown context package generation without raw repository dumps.
- [ ] Verify tests pass.

### Task 4: Parsing and Storage

**Files:**
- Create: `ohara/parsers/json_parser.py`
- Create: `ohara/storage/filesystem.py`

- [ ] Write failing tests for fenced JSON, prose-wrapped JSON, malformed trailing comma recovery, validation failure, and filesystem run artifacts.
- [ ] Implement strict JSON extraction and Pydantic validation.
- [ ] Implement filesystem run storage for context markdown, raw response, validated JSON, logs, and history metadata.
- [ ] Verify tests pass.

### Task 5: Automation and Orchestration

**Files:**
- Create: `ohara/automation/base.py`
- Create: `ohara/automation/chatgpt.py`
- Create: `ohara/reviews/orchestrator.py`

- [ ] Write failing tests using a fake review provider.
- [ ] Implement provider protocol and Playwright ChatGPT provider scaffold.
- [ ] Implement `ReviewRunner` orchestration for dry-run, no-browser, and provider-backed runs.
- [ ] Verify tests pass.

### Task 6: Documentation and Final Verification

**Files:**
- Create: `README.md`
- Create: `docs/architecture.md`
- Create: `docs/execution-flow.md`
- Create: `docs/extensions.md`
- Create: `docs/templates.md`
- Create: `docs/configuration.md`

- [ ] Document architecture, execution flow, template authoring, configuration, and future skill integration.
- [ ] Run `uv run python -m pytest`.
- [ ] Run `uv run ruff check .`.
- [ ] Run `uv run python -m ohara --help`.
- [ ] Run `uv run ohara:review run --template architecture-review --repo . --dry-run`.
