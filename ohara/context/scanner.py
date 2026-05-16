from __future__ import annotations

import json
import re
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from ohara.context.models import (
    FileInsight,
    RepositorySummary,
    RiskInsight,
    ScanResult,
    TodoInsight,
)

DEFAULT_EXCLUDES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".next",
    "coverage",
}
IMPORTANT_NAMES = {
    "README.md",
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "tsconfig.json",
    "Dockerfile",
    "docker-compose.yml",
    "compose.yml",
    "Cargo.toml",
    "go.mod",
}
IMPORTANT_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".go",
    ".rs",
    ".md",
    ".toml",
    ".json",
    ".yml",
    ".yaml",
}
TODO_RE = re.compile(r"\b(TODO|FIXME|HACK):?\s*(.*)", re.IGNORECASE)
SECRET_RE = re.compile(r"\b(password|secret|api[_-]?key|token)\b\s*=", re.IGNORECASE)


@dataclass
class RepositoryScanner:
    include: list[str] | None = None
    exclude: list[str] = field(default_factory=list)
    max_files: int = 400
    max_file_bytes: int = 512_000

    def scan(self, repositories: Iterable[Path]) -> ScanResult:
        summaries = [self._scan_repository(Path(repo).resolve()) for repo in repositories]
        return ScanResult(repositories=summaries)

    def _scan_repository(self, repo: Path) -> RepositorySummary:
        files = list(self._iter_files(repo))
        dependencies = sorted(self._detect_dependencies(repo, files))
        frameworks = self._detect_frameworks(files, dependencies)
        stack = self._detect_stack(files, dependencies, frameworks)
        todos, risks = self._scan_text_insights(repo, files)
        important_files = self._important_files(repo, files)
        tree = [str(path.relative_to(repo)) for path in files[: self.max_files]]
        return RepositorySummary(
            path=repo,
            name=repo.name,
            frameworks=frameworks,
            dependencies=dependencies,
            stack=stack,
            important_files=important_files,
            todos=todos,
            risks=risks,
            directory_tree=tree,
        )

    def _iter_files(self, repo: Path) -> Iterable[Path]:
        excludes = DEFAULT_EXCLUDES | set(self.exclude)
        collected = 0
        for path in sorted(repo.rglob("*")):
            if collected >= self.max_files:
                break
            if not path.is_file():
                continue
            rel_parts = path.relative_to(repo).parts
            if any(part in excludes for part in rel_parts):
                continue
            if path.stat().st_size > self.max_file_bytes:
                continue
            if self.include and not any(path.match(pattern) for pattern in self.include):
                continue
            collected += 1
            yield path

    def _detect_dependencies(self, repo: Path, files: list[Path]) -> set[str]:
        dependencies: set[str] = set()
        for path in files:
            if path.name == "pyproject.toml":
                dependencies.update(self._read_pyproject_dependencies(path))
            elif path.name == "requirements.txt":
                dependencies.update(self._read_requirements(path))
            elif path.name == "package.json":
                dependencies.update(self._read_package_json(path))
            elif path.name == "go.mod":
                dependencies.add("go")
            elif path.name == "Cargo.toml":
                dependencies.add("rust")
        return dependencies

    def _read_pyproject_dependencies(self, path: Path) -> set[str]:
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            return set()
        project_dependencies = data.get("project", {}).get("dependencies", [])
        return {self._normalize_dependency(item) for item in project_dependencies}

    def _read_requirements(self, path: Path) -> set[str]:
        dependencies: set[str] = set()
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                dependencies.add(self._normalize_dependency(line))
        return dependencies

    def _read_package_json(self, path: Path) -> set[str]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return set()
        dependencies = set(data.get("dependencies", {})) | set(data.get("devDependencies", {}))
        return {dependency.lower() for dependency in dependencies}

    def _normalize_dependency(self, dependency: str) -> str:
        return re.split(r"[<>=\[\] ;]", dependency, maxsplit=1)[0].strip().lower()

    def _detect_frameworks(self, files: list[Path], dependencies: set[str]) -> list[str]:
        frameworks: set[str] = set()
        dependency_map = {
            "fastapi": "FastAPI",
            "django": "Django",
            "flask": "Flask",
            "next": "Next.js",
            "react": "React",
            "vue": "Vue",
            "svelte": "Svelte",
            "pytest": "pytest",
        }
        for dependency, label in dependency_map.items():
            if dependency in dependencies:
                frameworks.add(label)
        for path in files:
            if path.suffix == ".py":
                text = path.read_text(encoding="utf-8", errors="ignore")[:20_000]
                if "from fastapi import" in text or "import fastapi" in text:
                    frameworks.add("FastAPI")
        return sorted(frameworks)

    def _detect_stack(
        self,
        files: list[Path],
        dependencies: set[str],
        frameworks: list[str],
    ) -> list[str]:
        stack = set(frameworks)
        if any(path.suffix == ".py" for path in files):
            stack.add("Python")
        if any(path.name == "package.json" for path in files):
            stack.add("JavaScript/TypeScript")
        if "pydantic" in dependencies:
            stack.add("Pydantic")
        return sorted(stack)

    def _scan_text_insights(
        self,
        repo: Path,
        files: list[Path],
    ) -> tuple[list[TodoInsight], list[RiskInsight]]:
        todos: list[TodoInsight] = []
        risks: list[RiskInsight] = []
        for path in files:
            if path.suffix not in IMPORTANT_SUFFIXES:
                continue
            try:
                lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                continue
            rel = str(path.relative_to(repo))
            for index, line in enumerate(lines, start=1):
                if match := TODO_RE.search(line):
                    text = f"{match.group(1).upper()}: {match.group(2).strip()}".rstrip()
                    todos.append(TodoInsight(path=rel, line=index, text=text))
                if SECRET_RE.search(line):
                    risks.append(
                        RiskInsight(
                            kind="secret",
                            path=rel,
                            line=index,
                            description="Potential hard-coded secret or credential assignment.",
                        )
                    )
        return todos[:50], risks[:50]

    def _important_files(self, repo: Path, files: list[Path]) -> list[FileInsight]:
        insights: list[FileInsight] = []
        for path in files:
            relative = str(path.relative_to(repo))
            reason = ""
            priority = 100
            if path.name in IMPORTANT_NAMES:
                reason = "project metadata or documentation"
                priority = 10
            elif path.suffix in {".py", ".ts", ".tsx", ".go", ".rs"}:
                reason = "source file"
                priority = 40
            elif path.suffix in {".yml", ".yaml"}:
                reason = "configuration"
                priority = 30
            if reason:
                insights.append(
                    FileInsight(
                        path=path,
                        relative_path=relative,
                        reason=reason,
                        size_bytes=path.stat().st_size,
                        priority=priority,
                    )
                )
        return sorted(insights, key=lambda item: (item.priority, item.relative_path))[:80]
