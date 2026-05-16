from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from ohara.reviews.orchestrator import ReviewRunner
from ohara.templates.registry import list_templates

app = typer.Typer(
    name="ohara:review",
    help="Run deep repository reviews through Ohara.",
    no_args_is_help=True,
)
console = Console()


@app.command("templates")
def templates() -> None:
    """List available review templates."""
    for template_name in list_templates():
        console.print(template_name)


@app.command("run")
def run(
    template: Annotated[str, typer.Option("--template", help="Review template name.")],
    repo: Annotated[
        list[Path] | None,
        typer.Option("--repo", "-r", help="Repository path. May be provided multiple times."),
    ] = None,
    output: Annotated[Path, typer.Option("--output", "-o")] = Path(".ohara/reviews"),
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Generate context without browser use."),
    ] = False,
    no_browser: Annotated[
        bool,
        typer.Option("--no-browser", help="Do not open ChatGPT."),
    ] = False,
) -> None:
    """Run a repository review."""
    repositories = repo or [Path.cwd()]
    runner = ReviewRunner(output_dir=output)
    result = runner.run(
        template_name=template,
        repositories=repositories,
        dry_run=dry_run,
        use_browser=not no_browser,
    )

    if result.parsed is None:
        console.print(
            Panel.fit(
                f"Context package written to {result.run_path / 'context.md'}",
                title="Ohara Review",
            )
        )
        return

    console.print(
        Panel.fit(
            f"Review JSON written to {result.run_path / 'review.json'}\n"
            f"Risk: {result.parsed.overall_risk}",
            title="Ohara Review",
        )
    )


if __name__ == "__main__":
    app()
