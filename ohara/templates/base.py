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

    def render_prompt(self, context_markdown: str, context_delivery: str = "inline") -> str:
        focus = "\n".join(f"- {item}" for item in self.focus_areas)
        priorities = "\n".join(f"- {item}" for item in self.context_priorities)
        extras = "\n".join(f"- {item}" for item in self.extra_instructions)
        context_instruction = (
            "The uploaded markdown file contains the repository context. "
            "Review only that context and cite evidence from it."
            if context_delivery == "uploaded"
            else "The repository context is included below. Review only this context and "
            "cite evidence from it."
        )
        secret_instruction = (
            "For detected secrets, treat regex matches as triage candidates unless literal "
            "credential material is shown."
        )
        return f"""# Ohara Review Template: {self.name}

## Objective
{self.objective}

## Context Source
{context_instruction}

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
  "critical_issues": [
    {{
      "title": "specific evidence-backed finding",
      "severity": "low|medium|high|critical",
      "evidence": ["quote or summarized evidence from the context"],
      "impact": "concrete repo-specific impact",
      "recommendation": "specific implementation recommendation",
      "codex_hint": "actionable hint for Codex",
      "confidence": "high|medium|low",
      "source_paths": []
    }}
  ],
  "technical_debt": [],
  "security_risks": [],
  "scalability_issues": [],
  "architecture_feedback": [],
  "implementation_plan": [],
  "quick_wins": [],
  "codex_actions": [],
  "recommended_execution_order": []
}}

Each finding must include title, severity, evidence, impact, recommendation, codex_hint,
confidence, and source_paths.
Each Codex action should be concrete enough for an implementation agent.
Avoid generic advice unless it is directly supported by evidence in the context.
Call out uncertainty when evidence is weak.
Distinguish confirmed findings from scanner heuristics.
{secret_instruction}

## Extra Instructions
{extras or "- No extra instructions."}

## Repository Context
{context_markdown}
"""
