# Ohara Architecture

Ohara is structured as a long-term skill ecosystem. V1 only implements `ohara:review`, but the shared modules are intentionally reusable by future skills such as `ohara:plan`, `ohara:context`, `ohara:security`, `ohara:map`, and `ohara:refactor`.

```text
ohara/
  automation/   browser provider protocol and ChatGPT Playwright CLI provider
  cli/          Typer command surfaces
  config/       typed runtime configuration models
  context/      repository scanner and markdown context builder
  parsers/      strict JSON extraction, repair, and validation
  reviews/      review orchestration
  schemas/      Pydantic machine-consumable output models
  storage/      filesystem run artifacts and history
  templates/    modular review templates
  utils/        small shared helpers
```

## Boundaries

`ReviewRunner` is the orchestration boundary. It does not know browser details, template internals, or parser repair mechanics. It coordinates stable interfaces:

- `RepositoryScanner.scan(paths) -> ScanResult`
- `ContextBuilder.build(scan) -> markdown`
- `ReviewTemplate.render_prompt(context) -> prompt`
- `BrowserReviewProvider.submit_review(request) -> response`
- `ReviewJsonParser.parse(raw) -> ReviewOutput`
- `FileSystemStorage.save_*() -> StoredRun`

This keeps the core review workflow testable without browser login state.

## Browser Automation

`ChatGPTPlaywrightCliProvider` shells out to Microsoft `@playwright/cli`. It uses a named session and persistent profile so authenticated ChatGPT sessions can be reused:

```bash
playwright-cli -s=ohara-chatgpt open https://chatgpt.com/ --persistent --profile=.ohara/playwright-cli-profile --headed
```

Selectors and CLI scripts are intentionally isolated in one provider because ChatGPT UI details are likely to change. Ohara does not use Playwright MCP for V1.

## Data Philosophy

Markdown context is optimized for reasoning quality. It starts with a repository briefing,
repository guidance summaries, review-mode rules, and high-signal source summaries before
falling back to directory inventory. It does not dump raw repository files.

The scanner is deterministic and heuristic-based. It detects stack and framework signals
from manifests and layout, summarizes representative entrypoints and configuration files,
and labels TODOs, possible secrets, and generated-file exclusions as scanner heuristics
instead of confirmed findings.

JSON output is optimized for machine consumption. Pydantic schemas reject unknown data,
enforce a known risk vocabulary, and require each finding to include confidence and source
paths.
