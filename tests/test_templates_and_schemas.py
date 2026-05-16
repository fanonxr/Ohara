import pytest
from pydantic import ValidationError

from ohara.schemas.review import ReviewOutput
from ohara.templates.registry import get_template, list_templates


def test_builtin_templates_are_available() -> None:
    assert list_templates() == [
        "architecture-review",
        "security-audit",
        "startup-readiness",
    ]
    template = get_template("architecture-review")
    assert template.objective
    assert "STRICT VALID JSON" in template.render_prompt("context")


def test_review_output_schema_requires_strict_top_level_fields() -> None:
    payload = {
        "template": "architecture-review",
        "summary": "Repository is coherent but needs clearer module boundaries.",
        "overall_risk": "medium",
        "critical_issues": [],
        "technical_debt": [],
        "security_risks": [],
        "scalability_issues": [],
        "architecture_feedback": [],
        "implementation_plan": [],
        "quick_wins": [],
        "codex_actions": [],
        "recommended_execution_order": [],
    }

    parsed = ReviewOutput.model_validate(payload)

    assert parsed.template == "architecture-review"
    assert parsed.overall_risk == "medium"


def test_review_finding_requires_confidence_and_source_paths() -> None:
    payload = {
        "template": "architecture-review",
        "summary": "Repository is coherent but needs clearer module boundaries.",
        "overall_risk": "medium",
        "critical_issues": [
            {
                "title": "Router bypasses boundary",
                "severity": "medium",
                "evidence": ["src/router.rs wires handlers directly"],
                "impact": "Changes are harder to isolate.",
                "recommendation": "Move composition behind module APIs.",
                "codex_hint": "Inspect src/router.rs before editing modules.",
                "confidence": "high",
                "source_paths": ["src/router.rs"],
            }
        ],
        "technical_debt": [],
        "security_risks": [],
        "scalability_issues": [],
        "architecture_feedback": [],
        "implementation_plan": [],
        "quick_wins": [],
        "codex_actions": [],
        "recommended_execution_order": [],
    }

    parsed = ReviewOutput.model_validate(payload)

    assert parsed.critical_issues[0].confidence == "high"
    assert parsed.critical_issues[0].source_paths == ["src/router.rs"]


def test_review_finding_rejects_missing_confidence_and_source_paths() -> None:
    with pytest.raises(ValidationError):
        ReviewOutput.model_validate(
            {
                "template": "architecture-review",
                "summary": "Invalid finding.",
                "overall_risk": "medium",
                "critical_issues": [
                    {
                        "title": "Generic issue",
                        "severity": "medium",
                        "evidence": ["No source paths supplied."],
                        "impact": "Unclear.",
                        "recommendation": "Be specific.",
                        "codex_hint": "Add evidence.",
                    }
                ],
                "technical_debt": [],
                "security_risks": [],
                "scalability_issues": [],
                "architecture_feedback": [],
                "implementation_plan": [],
                "quick_wins": [],
                "codex_actions": [],
                "recommended_execution_order": [],
            }
        )


def test_template_prompt_requires_evidence_grounded_review_and_context_mode_wording() -> None:
    prompt = get_template("security-audit").render_prompt(
        "## Repository Context",
        context_delivery="uploaded",
    )

    assert "The uploaded markdown file contains the repository context" in prompt
    assert "Avoid generic advice unless it is directly supported by evidence" in prompt
    assert "Call out uncertainty when evidence is weak" in prompt
    assert "Distinguish confirmed findings from scanner heuristics" in prompt
    assert "triage candidates unless literal credential material is shown" in prompt
    assert '"confidence": "high|medium|low"' in prompt
    assert '"source_paths": []' in prompt


def test_review_output_rejects_unknown_risk_level() -> None:
    with pytest.raises(ValidationError):
        ReviewOutput.model_validate(
            {
                "template": "architecture-review",
                "summary": "Invalid risk.",
                "overall_risk": "urgent",
                "critical_issues": [],
                "technical_debt": [],
                "security_risks": [],
                "scalability_issues": [],
                "architecture_feedback": [],
                "implementation_plan": [],
                "quick_wins": [],
                "codex_actions": [],
                "recommended_execution_order": [],
            }
        )
