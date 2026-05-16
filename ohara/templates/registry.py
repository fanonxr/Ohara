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
    "design-review": ReviewTemplate(
        name="design-review",
        objective=(
            "Audit the visual design system, UX architecture, and perceived product "
            "quality of a client application (typically Flutter or React Native) "
            "against the bar set by premium social platforms (X, Threads, Instagram, "
            "Reddit, Quora). Identify weak visual patterns, generic UI, inconsistent "
            "spacing, low hierarchy clarity, outdated interactions, and low perceived "
            "quality areas. Extract the current theme/token structure so it can be "
            "redesigned against."
        ),
        focus_areas=[
            "typography choices, ramp, weights, pairings, and tracking",
            "spacing scale, rhythm, and alignment across screens",
            "color system: layering, contrast, semantic tokens, and dark/light parity",
            "iconography consistency, weight, and grid alignment",
            "component composition: reuse, primitives vs ad-hoc widgets, prop hygiene",
            "navigation structure, tab/shell pattern, and route topology",
            "information density per screen (feed, profile, discover, composer)",
            "animation/motion usage: durations, curves, transitions, micro-interactions",
            "gesture vocabulary and platform-native feel",
            "loading, empty, error, and skeleton state quality",
            "what reads as generic Material-default vs intentional brand expression",
            "accessibility floor: contrast, touch targets, text scaling",
        ],
        context_priorities=[
            "design tokens (colors, typography, spacing, motion)",
            "theme extensions and Material/Cupertino theming setup",
            "reusable component primitives (buttons, cards, chips, inputs, sheets)",
            "navigation shell and tab structure",
            "key feature screens (feed, profile, discover, composer, messages, onboarding)",
            "animation/motion usage and shared transition widgets",
            "icon set and asset directory",
            "platform-specific overrides (iOS vs Android)",
        ],
        implementation_philosophy=(
            "Surface bold, opinionated redesign opportunities. Distinguish surface "
            "polish from structural redesigns. Call out generic Material defaults "
            "explicitly. Compare patterns to premium social platforms by name when "
            "relevant. Favor systemic fixes (token-level, primitive-level) over "
            "screen-by-screen patches."
        ),
        extra_instructions=[
            "Treat every finding as design-quality, not architectural-quality.",
            "When you spot a generic pattern, name what would replace it and which reference app does it well.",
            "Cite specific file paths and widget names from the context as evidence.",
            "Flag inconsistencies between the documented design system and how screens actually consume it.",
            "Distinguish 'weak visual pattern' (cosmetic) from 'weak structural pattern' (architectural).",
        ],
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
