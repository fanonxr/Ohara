from __future__ import annotations

import typer

from ohara.cli import review

app = typer.Typer(
    name="ohara",
    help="Repository intelligence and deep review tools for Codex workflows.",
    no_args_is_help=True,
)
app.add_typer(review.app, name="review")
