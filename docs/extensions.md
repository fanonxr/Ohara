# Extension Guide

Future Ohara skills should reuse the V1 platform pieces instead of reimplementing repository analysis.

## Adding a New Skill

1. Add a new orchestration module, for example `ohara/plans/orchestrator.py`.
2. Reuse `RepositoryScanner` and `ContextBuilder` unless the skill needs a specialized context package.
3. Add skill-specific templates in `ohara/templates` or a dedicated registry.
4. Define strict Pydantic output schemas in `ohara/schemas`.
5. Persist artifacts through `FileSystemStorage` or a storage adapter with the same run-directory semantics.
6. Add a Typer command under `ohara/cli`.

## Future Skills

- `ohara:plan` should transform review JSON into implementation plans.
- `ohara:context` should generate standalone context packages for arbitrary Codex sessions.
- `ohara:security` should specialize scanner rules and schemas for security review.
- `ohara:map` should build repository maps and ownership graphs.
- `ohara:refactor` should consume review output and produce Codex-ready refactor sequences.

## Provider Evolution

The automation provider protocol is intentionally small:

```python
async def submit_review(request: ReviewRequest) -> ReviewResponse:
    ...
```

That is enough for the current Playwright CLI provider or a future desktop automation provider.
