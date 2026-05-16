# Template Guide

Templates live in `ohara/templates/registry.py` and are represented by `ReviewTemplate`.

Each template defines:

- `name`
- `objective`
- `focus_areas`
- `context_priorities`
- `implementation_philosophy`
- strict JSON output instructions

Template prompts require evidence-grounded findings. They tell ChatGPT to avoid generic
advice unless supported by context, call out weak evidence, distinguish confirmed findings
from scanner heuristics, and treat secret regex matches as triage candidates unless literal
credential material is shown.

## V1 Templates

### architecture-review

Focuses on architecture boundaries, coupling, dependency direction, maintainability, testability, and change safety.

### security-audit

Focuses on credentials, authentication, authorization, dependency risk, configuration risk, logging, and data exposure.

### startup-readiness

Focuses on delivery velocity, production readiness, operational maturity, highest leverage fixes, and quick wins.

## Adding Templates

Add a new `ReviewTemplate` to `TEMPLATES` and a test that confirms `list_templates()`
includes it and `render_prompt()` includes strict JSON instructions, confidence, source
paths, and evidence-grounding guidance.
