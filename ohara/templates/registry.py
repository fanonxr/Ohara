from __future__ import annotations

from ohara.templates.base import ReviewTemplate

TEMPLATES: dict[str, ReviewTemplate] = {
    "architecture-review": ReviewTemplate(
        name="architecture-review",
        objective=(
            "Assess architecture quality, module boundaries, maintainability, "
            "and evolution risk."
        ),
        focus_areas=[
            "system boundaries and coupling",
            "dependency direction and layering",
            "testability and change safety",
            "operational clarity",
        ],
        context_priorities=[
            "project metadata",
            "entrypoints and application structure",
            "important source files",
            "TODOs and detected risks",
        ],
        implementation_philosophy=(
            "Prefer incremental refactors that improve clarity and reduce risk "
            "without broad rewrites."
        ),
    ),
    "security-audit": ReviewTemplate(
        name="security-audit",
        objective=(
            "Identify security risks, unsafe defaults, credential exposure, "
            "and hardening gaps."
        ),
        focus_areas=[
            "credential handling",
            "authentication and authorization boundaries",
            "dependency and configuration risks",
            "data exposure and logging risks",
        ],
        context_priorities=[
            "configuration files",
            "dependency manifests",
            "security-sensitive source files",
            "detected secret patterns",
        ],
        implementation_philosophy=(
            "Prioritize exploitable risks and concrete mitigations over speculative issues."
        ),
    ),
    "startup-readiness": ReviewTemplate(
        name="startup-readiness",
        objective=(
            "Evaluate whether the repository is ready for rapid product iteration "
            "and production use."
        ),
        focus_areas=[
            "delivery velocity",
            "operational readiness",
            "maintainability",
            "highest leverage fixes",
        ],
        context_priorities=[
            "documentation",
            "build and dependency metadata",
            "tests and deployment signals",
            "quick wins",
        ],
        implementation_philosophy=(
            "Recommend the smallest changes that unlock reliability, speed, and product learning."
        ),
    ),
}


def list_templates() -> list[str]:
    return sorted(TEMPLATES)


def get_template(name: str) -> ReviewTemplate:
    try:
        return TEMPLATES[name]
    except KeyError as exc:
        available = ", ".join(list_templates())
        raise ValueError(f"Unknown review template '{name}'. Available: {available}") from exc
