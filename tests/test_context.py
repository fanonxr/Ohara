from pathlib import Path

from ohara.context.builder import ContextBuilder
from ohara.context.scanner import RepositoryScanner


def test_scanner_detects_stack_dependencies_todos_and_ignores_noise(tmp_path: Path) -> None:
    repo = tmp_path / "service"
    repo.mkdir()
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "service"\ndependencies = ["fastapi", "pydantic"]\n',
        encoding="utf-8",
    )
    (repo / "app.py").write_text(
        "from fastapi import FastAPI\n# TODO: add auth\npassword = 'secret'\n",
        encoding="utf-8",
    )
    ignored = repo / ".venv"
    ignored.mkdir()
    (ignored / "noise.py").write_text("print('ignore')", encoding="utf-8")

    result = RepositoryScanner().scan([repo])

    assert result.repositories[0].frameworks == ["FastAPI"]
    assert "fastapi" in result.repositories[0].dependencies
    assert "pydantic" in result.repositories[0].dependencies
    assert any(item.text == "TODO: add auth" for item in result.repositories[0].todos)
    assert any(risk.kind == "secret" for risk in result.repositories[0].risks)
    assert all(".venv" not in str(file.path) for file in result.repositories[0].important_files)


def test_context_builder_creates_reasoning_markdown_without_raw_repo_dump(tmp_path: Path) -> None:
    repo = tmp_path / "web"
    repo.mkdir()
    (repo / "package.json").write_text(
        '{"dependencies":{"next":"latest","react":"latest"}}',
        encoding="utf-8",
    )
    (repo / "README.md").write_text("A web app.\n", encoding="utf-8")

    scan = RepositoryScanner().scan([repo])
    markdown = ContextBuilder().build(scan)

    assert "# Ohara Repository Context Package" in markdown
    assert "## Repository: web" in markdown
    assert "Next.js" in markdown
    assert "package.json" in markdown
    assert '{"dependencies"' not in markdown
