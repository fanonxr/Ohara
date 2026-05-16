from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReviewTemplate:
    name: str
    objective: str
    focus_areas: list[str]
    context_priorities: list[str]
    implementation_philosophy: str
    output_schema_name: str = "ReviewOutput"
    extra_instructions: list[str] = field(default_factory=list)

    def render_prompt(self, context_markdown: str) -> str:
        focus = "\n".join(f"- {item}" for item in self.focus_areas)
        priorities = "\n".join(f"- {item}" for item in self.context_priorities)
        extras = "\n".join(f"- {item}" for item in self.extra_instructions)
        return f"""# Ohara Review Template: {self.name}

## Objective
{self.objective}

## Focus Areas
{focus}

## Context Prioritization
{priorities}

## Implementation Philosophy
{self.implementation_philosophy}

## Output Requirements
Return ONLY STRICT VALID JSON. Do not include markdown fences, comments, prose, or trailing commas.
The JSON must match this schema shape exactly:

{{
  "template": "{self.name}",
  "summary": "short executive technical summary",
  "overall_risk": "low|medium|high|critical",
  "critical_issues": [],
  "technical_debt": [],
  "security_risks": [],
  "scalability_issues": [],
  "architecture_feedback": [],
  "implementation_plan": [],
  "quick_wins": [],
  "codex_actions": [],
  "recommended_execution_order": []
}}

Each finding should include title, severity, evidence, impact, recommendation, and codex_hint.
Each Codex action should be concrete enough for an implementation agent.

## Extra Instructions
{extras or "- No extra instructions."}

## Repository Context
{context_markdown}
"""
