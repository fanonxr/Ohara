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
