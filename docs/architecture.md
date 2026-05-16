# Ohara Architecture

Ohara is structured as a long-term skill ecosystem. V1 only implements `ohara:review`, but the shared modules are intentionally reusable by future skills such as `ohara:plan`, `ohara:context`, `ohara:security`, `ohara:map`, and `ohara:refactor`.

```text
ohara/
  automation/   browser provider protocol and ChatGPT Playwright provider
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

`ChatGPTPlaywrightProvider` uses a persistent browser profile so authenticated ChatGPT sessions can be reused. Selectors are intentionally isolated in one provider because ChatGPT UI details are likely to change. Future providers can support Playwright MCP or desktop automation without changing scanner, templates, parser, storage, or CLI code.

## Data Philosophy

Markdown context is optimized for reasoning quality. It summarizes stack, dependencies, important files, directory structure, TODOs, risks, and system descriptions. It does not dump raw repository files.

JSON output is optimized for machine consumption. Pydantic schemas reject unknown top-level data and enforce a known risk vocabulary.
