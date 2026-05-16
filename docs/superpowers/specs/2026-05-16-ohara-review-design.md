# Ohara Review V1 Design

## Objective

Ohara V1 implements `ohara:review`, an extensible repository intelligence skill for Codex workflows. It scans one or more repositories, builds compact markdown context packages, submits them to ChatGPT through Playwright browser automation, parses strict JSON review output, and persists results for downstream Codex implementation work.

V1 deliberately avoids the OpenAI API. Browser automation is the integration boundary for ChatGPT Pro models.

## Scope

Implemented in V1:

- Python 3.12+ package managed by `uv`
- Typer CLI with `ohara:review run`
- Recursive multi-repo scanner with include/exclude rules
- framework, dependency, stack, TODO, and risk detection
- LLM-optimized markdown context package builder
- modular templates for `architecture-review`, `security-audit`, and `startup-readiness`
- Playwright automation provider interface plus a ChatGPT provider scaffold
- strict JSON extraction, recovery, Pydantic validation, and persistence
- filesystem storage for context, raw response, validated JSON, logs, and history metadata
- documentation for architecture, execution flow, templates, and extensions

Not implemented in V1:

- embeddings or vector databases
- OpenAI API usage
- autonomous code modification
- browser-specific selector guarantees across all future ChatGPT UI changes
- future skills such as `ohara:plan`, `ohara:context`, `ohara:security`, `ohara:map`, or `ohara:refactor`

## Architecture

The system is a set of small modules connected by the `ReviewRunner` orchestration layer.

```text
CLI -> ReviewRunner
       -> RepositoryScanner
       -> ContextBuilder
       -> ReviewTemplateRegistry
       -> BrowserReviewProvider
       -> ReviewJsonParser
       -> FileSystemStorage
```

The scanner and context builder are offline-testable and deterministic. The automation layer is provider-based so V1 can support Playwright now and later add Playwright MCP, desktop automation, or multiple browser profiles without rewriting review orchestration.

## Data Flow

1. User runs `ohara:review run --template architecture-review`.
2. The CLI resolves one or more repository paths and loads runtime options.
3. The scanner walks each repository with default and user-provided ignore rules.
4. The scanner identifies important files, frameworks, dependencies, TODOs, and risks.
5. The context builder emits a compact markdown package optimized for model reasoning.
6. The template builds a specialized prompt with strict JSON instructions.
7. The automation provider uploads/submits context and prompt to ChatGPT.
8. The parser extracts and validates JSON against the review schema.
9. Storage writes markdown context, raw response, parsed JSON, and run metadata.

## Error Handling

Scanner errors are isolated per file so unreadable files do not fail a whole run. Parser errors include repair attempts for fenced JSON, preamble text, and trailing prose. Automation failures are returned as provider errors with enough metadata for the CLI to show the failed phase. Storage writes are grouped in a run directory so partial results remain inspectable.

## Testing

Tests cover scanner behavior, context compression, template availability, strict JSON parsing and recovery, storage writes, orchestration with a fake provider, and the Typer CLI. Browser automation is designed behind an interface so core tests do not require logging into ChatGPT.

## Extension Points

Future `ohara:*` skills should reuse scanner, context packages, template registry, schemas, and storage. Each new skill should add its own orchestration module and schema while preserving the common provider and parser boundaries.
