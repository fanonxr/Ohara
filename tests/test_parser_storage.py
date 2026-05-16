from pathlib import Path

import pytest

from ohara.parsers.json_parser import ReviewJsonParser, ReviewParseError
from ohara.storage.filesystem import FileSystemStorage

VALID_JSON = """
```json
{
  "template": "architecture-review",
  "summary": "Solid base.",
  "overall_risk": "low",
  "critical_issues": [],
  "technical_debt": [],
  "security_risks": [],
  "scalability_issues": [],
  "architecture_feedback": [],
  "implementation_plan": [],
  "quick_wins": [],
  "codex_actions": [],
  "recommended_execution_order": []
}
```
"""


def test_parser_extracts_fenced_json() -> None:
    parsed = ReviewJsonParser().parse(VALID_JSON)

    assert parsed.summary == "Solid base."


def test_parser_recovers_prose_wrapped_json_with_trailing_commas() -> None:
    raw = """Here is the review:
{
  "template": "security-audit",
  "summary": "Needs hardening.",
  "overall_risk": "high",
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
Thanks."""

    parsed = ReviewJsonParser().parse(raw)

    assert parsed.template == "security-audit"


def test_parser_raises_for_invalid_schema() -> None:
    with pytest.raises(ReviewParseError):
        ReviewJsonParser().parse('{"template": "x"}')


def test_storage_writes_run_artifacts(tmp_path: Path) -> None:
    storage = FileSystemStorage(tmp_path)
    parsed = ReviewJsonParser().parse(VALID_JSON)

    run = storage.save_review(
        template="architecture-review",
        context_markdown="# Context",
        raw_response=VALID_JSON,
        parsed=parsed,
        logs=["created"],
    )

    assert (run.path / "context.md").read_text(encoding="utf-8") == "# Context"
    assert (run.path / "raw-response.md").exists()
    assert (run.path / "review.json").exists()
    assert (run.path / "logs.txt").read_text(encoding="utf-8") == "created\n"
    assert (tmp_path / "history.jsonl").exists()
