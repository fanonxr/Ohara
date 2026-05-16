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


def test_scanner_detects_polyglot_monorepo_without_incidental_python(tmp_path: Path) -> None:
    repo = tmp_path / "product"
    (repo / "backend" / "src").mkdir(parents=True)
    (repo / "mobile" / "lib").mkdir(parents=True)
    (repo / "web").mkdir()
    (repo / "infra").mkdir()
    (repo / "scripts").mkdir()
    (repo / ".github" / "workflows").mkdir(parents=True)
    (repo / "Cargo.toml").write_text(
        '[workspace]\nmembers = ["backend"]\n',
        encoding="utf-8",
    )
    (repo / "backend" / "Cargo.toml").write_text(
        '[package]\nname = "api"\nversion = "0.1.0"\n'
        '[dependencies]\naxum = "0.7"\nsqlx = "0.8"\ntokio = "1"\n',
        encoding="utf-8",
    )
    (repo / "backend" / "src" / "main.rs").write_text(
        "use axum::Router;\n#[tokio::main]\nasync fn main() {}\n",
        encoding="utf-8",
    )
    (repo / "mobile" / "pubspec.yaml").write_text(
        "dependencies:\n  flutter:\n    sdk: flutter\n",
        encoding="utf-8",
    )
    (repo / "mobile" / "lib" / "main.dart").write_text(
        "import 'package:flutter/material.dart';\nvoid main() {}\n",
        encoding="utf-8",
    )
    (repo / "web" / "package.json").write_text(
        '{"dependencies":{"next":"latest","react":"latest","tailwindcss":"latest"}}',
        encoding="utf-8",
    )
    (repo / "web" / "tailwind.config.ts").write_text("export default {}", encoding="utf-8")
    (repo / "infra" / "main.tf").write_text('module "app" { source = "./app" }\n', encoding="utf-8")
    (repo / ".github" / "workflows" / "ci.yml").write_text("name: CI\n", encoding="utf-8")
    (repo / "docker-compose.yml").write_text(
        "services:\n  api:\n    build: backend\n",
        encoding="utf-8",
    )
    (repo / "scripts" / "helper.py").write_text("print('helper only')\n", encoding="utf-8")

    summary = RepositoryScanner().scan([repo]).repositories[0]

    assert {"Rust", "Dart/Flutter", "JavaScript/TypeScript", "Terraform"}.issubset(
        set(summary.stack)
    )
    expected_frameworks = {
        "Cargo workspace",
        "Axum",
        "sqlx",
        "Tokio",
        "Flutter",
        "Next.js",
        "React",
        "Tailwind CSS",
    }
    assert expected_frameworks.issubset(set(summary.frameworks))
    assert "Docker Compose" in summary.frameworks
    assert "GitHub Actions" in summary.frameworks
    assert "Python" not in summary.stack


def test_default_excludes_remove_noisy_generated_paths(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    noisy_files = [
        ".agents/skills/review/SKILL.md",
        ".sqlx/query-123.json",
        "mobile/lib/user.g.dart",
        "mobile/lib/user.freezed.dart",
        "node_modules/pkg/index.js",
        "web/.next/server/app.js",
        "build/generated/main.js",
        "assets/icon.png",
    ]
    for relative in noisy_files:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("noise", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "main.rs").write_text("fn main() {}\n", encoding="utf-8")

    summary = RepositoryScanner().scan([repo]).repositories[0]

    tree = "\n".join(summary.directory_tree)
    for relative in noisy_files:
        assert relative not in tree
    assert "src/main.rs" in tree
    assert {item.path for item in summary.excluded_paths} >= set(noisy_files)


def test_context_includes_compressed_repository_guidance(tmp_path: Path) -> None:
    repo = tmp_path / "guided"
    repo.mkdir()
    (repo / "AGENTS.md").write_text(
        "# Agent Rules\nUse TDD. Do not call the OpenAI API.\n" + "Do not dump this. " * 80,
        encoding="utf-8",
    )
    (repo / "CLAUDE.md").write_text(
        "# Claude Rules\nPrefer small patches and cite files.\n",
        encoding="utf-8",
    )
    (repo / "README.md").write_text("# Product\nA local review tool for Codex.\n", encoding="utf-8")

    scan = RepositoryScanner().scan([repo])
    markdown = ContextBuilder().build(scan, template_name="architecture-review")

    assert "### Repository Guidance" in markdown
    assert "`AGENTS.md`" in markdown
    assert "`CLAUDE.md`" in markdown
    assert "Use TDD" in markdown
    assert markdown.count("Do not dump this.") < 5


def test_architecture_and_security_contexts_prioritize_different_evidence(tmp_path: Path) -> None:
    repo = tmp_path / "app"
    (repo / "src").mkdir(parents=True)
    (repo / ".sqlx").mkdir()
    (repo / "docs" / "architecture").mkdir(parents=True)
    (repo / "docs" / "architecture" / "overview.md").write_text(
        "The router owns module boundaries.\n",
        encoding="utf-8",
    )
    (repo / "src" / "auth.rs").write_text(
        "pub fn authorize() {}\nlet token = std::env::var(\"TOKEN\");\n",
        encoding="utf-8",
    )
    (repo / ".sqlx" / "query.json").write_text('{"query":"select * from users"}', encoding="utf-8")

    architecture = ContextBuilder().build(
        RepositoryScanner(review_mode="architecture-review").scan([repo]),
        template_name="architecture-review",
    )
    security = ContextBuilder().build(
        RepositoryScanner(review_mode="security-audit").scan([repo]),
        template_name="security-audit",
    )

    assert "Architecture review context rules" in architecture
    assert "Security audit context rules" in security
    assert "module boundaries" in architecture
    assert "auth, authorization" in security
    assert ".sqlx/query.json" not in architecture
    assert ".sqlx/query.json" in security
