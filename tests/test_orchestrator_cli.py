import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ohara.automation.base import ReviewRequest, ReviewResponse
from ohara.automation.chatgpt import ChatGPTPlaywrightCliProvider
from ohara.cli.review import app
from ohara.parsers.json_parser import ReviewParseError
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


class InvalidJsonProvider:
    async def submit_review(self, request: ReviewRequest) -> ReviewResponse:
        return ReviewResponse(
            raw_text="ChatGPT UI text but no valid review JSON",
            model="fake",
            metadata={"mode": "invalid"},
        )


class FakeCliRunner:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []

    async def run(self, args: list[str]) -> str:
        self.commands.append(args)
        if "run-code" in args:
            return json.dumps(
                {
                    "template": "architecture-review",
                    "summary": "Reviewed.",
                    "overall_risk": "low",
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
        return ""


async def test_chatgpt_provider_uses_playwright_cli(tmp_path: Path) -> None:
    cli = FakeCliRunner()
    provider = ChatGPTPlaywrightCliProvider(
        command=("playwright-cli",),
        session="ohara-test",
        profile_dir=tmp_path / "profile",
        headed=True,
        runner=cli,
        script_dir=tmp_path / "scripts",
    )

    response = await provider.submit_review(
        ReviewRequest(
            template_name="architecture-review",
            prompt="Return JSON.",
            context_markdown="# Context",
            context_path=tmp_path / "context.md",
        )
    )

    assert response.metadata["provider"] == "chatgpt-playwright-cli"
    assert cli.commands[0][:3] == ["playwright-cli", "-s=ohara-test", "open"]
    assert "--persistent" in cli.commands[0]
    assert "--headed" in cli.commands[0]
    assert cli.commands[1][:4] == ["playwright-cli", "-s=ohara-test", "--raw", "run-code"]
    assert response.raw_text.startswith('{"template"')


def test_chatgpt_submit_script_verifies_prompt_and_clicks_send_button(tmp_path: Path) -> None:
    provider = ChatGPTPlaywrightCliProvider(script_dir=tmp_path / "scripts")

    script = provider._script_source(
        prompt="Return JSON.",
        inline_context="Return JSON.\n# Context",
        context_path=str(tmp_path / "context.md"),
    )

    assert "OHARA_SUBMIT_FAILED" in script
    assert "waitForPromptText" in script
    assert "button[aria-label=\"Send prompt\"]" in script
    assert "await sendButton.click()" in script
    assert "no assistant response started" in script
    assert "page.keyboard.press('Enter')" not in script


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


def test_review_runner_saves_raw_and_parse_error_when_provider_response_is_invalid(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("hello", encoding="utf-8")

    with pytest.raises(ReviewParseError):
        ReviewRunner(output_dir=tmp_path / "out", provider=InvalidJsonProvider()).run(
            template_name="architecture-review",
            repositories=[repo],
            dry_run=False,
            use_browser=True,
        )

    run_dirs = [path for path in (tmp_path / "out").iterdir() if path.is_dir()]
    assert len(run_dirs) == 1
    assert (run_dirs[0] / "raw-response.md").read_text(encoding="utf-8") == (
        "ChatGPT UI text but no valid review JSON"
    )
    assert "JSON object" in (run_dirs[0] / "parse-error.txt").read_text(encoding="utf-8")
    assert not (run_dirs[0] / "review.json").exists()


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
