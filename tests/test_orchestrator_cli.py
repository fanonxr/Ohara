from pathlib import Path

from typer.testing import CliRunner

from ohara.automation.base import ReviewRequest, ReviewResponse
from ohara.cli.review import app
from ohara.reviews.orchestrator import ReviewRunner


class FakeProvider:
    async def submit_review(self, request: ReviewRequest) -> ReviewResponse:
        assert request.template_name == "startup-readiness"
        return ReviewResponse(
            raw_text="""
            {
              "template": "startup-readiness",
              "summary": "Ready after a few fixes.",
              "overall_risk": "medium",
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
            """,
            model="fake",
            metadata={"mode": "test"},
        )


def test_review_runner_dry_run_saves_context_only(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("hello", encoding="utf-8")

    result = ReviewRunner(output_dir=tmp_path / "out").run(
        template_name="architecture-review",
        repositories=[repo],
        dry_run=True,
        use_browser=False,
    )

    assert result.parsed is None
    assert result.context_markdown.startswith("# Ohara Repository Context Package")
    assert (result.run_path / "context.md").exists()


def test_review_runner_uses_provider_and_saves_json(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("hello", encoding="utf-8")

    result = ReviewRunner(output_dir=tmp_path / "out", provider=FakeProvider()).run(
        template_name="startup-readiness",
        repositories=[repo],
        dry_run=False,
        use_browser=True,
    )

    assert result.parsed is not None
    assert result.parsed.template == "startup-readiness"
    assert (result.run_path / "review.json").exists()


def test_cli_dry_run(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("hello", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "run",
            "--template",
            "architecture-review",
            "--repo",
            str(repo),
            "--output",
            str(tmp_path / "out"),
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "Context package written" in result.output
