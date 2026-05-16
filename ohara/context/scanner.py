from __future__ import annotations

import json
import re
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from ohara.context.models import (
    BriefingInsight,
    ExcludedPath,
    FileInsight,
    GuidanceInsight,
    RepositorySummary,
    RiskInsight,
    ScanResult,
    SourceSummary,
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
    ".agents",
    ".ohara",
    ".playwright-cli",
}
SECURITY_OPTIONAL_EXCLUDES = {".sqlx"}
IMPORTANT_NAMES = {
    "AGENTS.md",
    "CLAUDE.md",
    "README.md",
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "tsconfig.json",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
    "Cargo.toml",
    "pubspec.yaml",
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
    ".dart",
    ".tf",
}
GENERATED_SUFFIXES = (".g.dart", ".freezed.dart")
ASSET_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".icns",
    ".svg",
    ".pdf",
}
TODO_RE = re.compile(r"(?:#|//|--|/\*|\*)?\s*\b(TODO|FIXME|HACK):\s*(.*)", re.IGNORECASE)
SECRET_RE = re.compile(r"\b(password|secret|api[_-]?key|token)\b\s*=", re.IGNORECASE)
GUIDANCE_PATH_RE = re.compile(
    r"^(AGENTS\.md|CLAUDE\.md|README\.md|docs/architecture/.+|docs/superpowers/specs/.+)$"
)


@dataclass
class RepositoryScanner:
    include: list[str] | None = None
    exclude: list[str] = field(default_factory=list)
    max_files: int = 400
    max_file_bytes: int = 512_000
    review_mode: str = "architecture-review"

    def scan(self, repositories: Iterable[Path]) -> ScanResult:
        summaries = [self._scan_repository(Path(repo).resolve()) for repo in repositories]
        return ScanResult(repositories=summaries)

    def _scan_repository(self, repo: Path) -> RepositorySummary:
        files, excluded_paths = self._collect_files(repo)
        dependencies = sorted(self._detect_dependencies(repo, files))
        frameworks = self._detect_frameworks(files, dependencies)
        stack = self._detect_stack(files, dependencies, frameworks)
        todos, risks = self._scan_text_insights(repo, files)
        important_files = self._important_files(repo, files)
        guidance = self._guidance(repo, files)
        source_summaries = self._source_summaries(repo, files)
        briefing = self._briefing(repo, files, stack, frameworks, guidance, source_summaries)
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
            guidance=guidance,
            briefing=briefing,
            source_summaries=source_summaries,
            excluded_paths=excluded_paths,
        )

    def _collect_files(self, repo: Path) -> tuple[list[Path], list[ExcludedPath]]:
        files: list[Path] = []
        excluded: list[ExcludedPath] = []
        collected = 0
        for path in sorted(repo.rglob("*")):
            if not path.is_file():
                continue
            relative = str(path.relative_to(repo))
            reason = self._exclude_reason(repo, path)
            if reason:
                excluded.append(ExcludedPath(path=relative, reason=reason))
                continue
            if collected >= self.max_files:
                continue
            try:
                size = path.stat().st_size
            except OSError:
                excluded.append(ExcludedPath(path=relative, reason="stat failed"))
                continue
            if size > self.max_file_bytes:
                excluded.append(ExcludedPath(path=relative, reason="file exceeds max_file_bytes"))
                continue
            if self.include and not any(path.match(pattern) for pattern in self.include):
                continue
            collected += 1
            files.append(path)
        return files, excluded[:200]

    def _exclude_reason(self, repo: Path, path: Path) -> str | None:
        excludes = DEFAULT_EXCLUDES | set(self.exclude)
        if self.review_mode != "security-audit":
            excludes |= SECURITY_OPTIONAL_EXCLUDES
        rel = path.relative_to(repo)
        rel_parts = rel.parts
        if any(part in excludes for part in rel_parts):
            return "default noisy/generated directory exclude"
        relative = str(rel)
        if relative.endswith(GENERATED_SUFFIXES):
            return "generated Dart source"
        if path.suffix.lower() in ASSET_SUFFIXES:
            return "platform asset or binary media"
        return None

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
                dependencies.update(self._read_cargo_dependencies(path))
            elif path.name == "pubspec.yaml":
                dependencies.update(self._read_pubspec_dependencies(path))
            elif path.suffix == ".tf":
                dependencies.add("terraform")
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

    def _read_cargo_dependencies(self, path: Path) -> set[str]:
        dependencies = {"rust"}
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            return dependencies
        if "workspace" in data:
            dependencies.add("cargo-workspace")
        for table in ("dependencies", "dev-dependencies", "build-dependencies"):
            dependencies.update(str(item).lower() for item in data.get(table, {}))
        return dependencies

    def _read_pubspec_dependencies(self, path: Path) -> set[str]:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return set()
        dependencies = {"dart"}
        if re.search(r"^\s*flutter\s*:", text, re.MULTILINE):
            dependencies.add("flutter")
        for match in re.finditer(r"^\s{2}([a-zA-Z0-9_]+)\s*:", text, re.MULTILINE):
            dependencies.add(match.group(1).lower())
        return dependencies

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
            "tailwindcss": "Tailwind CSS",
            "vue": "Vue",
            "svelte": "Svelte",
            "pytest": "pytest",
            "axum": "Axum",
            "sqlx": "sqlx",
            "tokio": "Tokio",
            "flutter": "Flutter",
            "cargo-workspace": "Cargo workspace",
            "terraform": "Terraform",
        }
        for dependency, label in dependency_map.items():
            if dependency in dependencies:
                frameworks.add(label)
        for path in files:
            if path.suffix == ".py":
                if "tests" in path.parts:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")[:20_000]
                if re.search(r"^\s*(from fastapi import|import fastapi)\b", text, re.MULTILINE):
                    frameworks.add("FastAPI")
            elif path.name.startswith("tailwind.config"):
                frameworks.add("Tailwind CSS")
            elif path.suffix == ".tf":
                frameworks.add("Terraform")
            elif path.name in {
                "docker-compose.yml",
                "docker-compose.yaml",
                "compose.yml",
                "compose.yaml",
            }:
                frameworks.add("Docker Compose")
            elif ".github/workflows/" in path.as_posix():
                frameworks.add("GitHub Actions")
            elif path.name == "pubspec.yaml" or path.suffix == ".dart":
                frameworks.add("Flutter")
        return sorted(frameworks)

    def _detect_stack(
        self,
        files: list[Path],
        dependencies: set[str],
        frameworks: list[str],
    ) -> list[str]:
        stack = set(frameworks)
        if self._has_python_project(files):
            stack.add("Python")
        if any(path.name == "package.json" for path in files):
            stack.add("JavaScript/TypeScript")
        if any(path.name == "Cargo.toml" for path in files) or "rust" in dependencies:
            stack.add("Rust")
        if any(path.name == "pubspec.yaml" for path in files) or "flutter" in dependencies:
            stack.add("Dart/Flutter")
        if any(path.suffix == ".tf" for path in files):
            stack.add("Terraform")
        if "pydantic" in dependencies:
            stack.add("Pydantic")
        return sorted(stack)

    def _has_python_project(self, files: list[Path]) -> bool:
        manifest_names = {"pyproject.toml", "requirements.txt", "setup.py", "setup.cfg", "Pipfile"}
        return any(path.name in manifest_names for path in files)

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
            elif path.suffix in {".dart", ".tf"}:
                reason = "source or infrastructure file"
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

    def _guidance(self, repo: Path, files: list[Path]) -> list[GuidanceInsight]:
        insights: list[GuidanceInsight] = []
        for path in files:
            relative = str(path.relative_to(repo))
            if not GUIDANCE_PATH_RE.match(relative):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            priority = 5 if path.name in {"AGENTS.md", "CLAUDE.md"} else 15
            insights.append(
                GuidanceInsight(
                    path=relative,
                    title=self._document_title(path, text),
                    summary=self._summarize_text(text, max_chars=420),
                    priority=priority,
                )
            )
        return sorted(insights, key=lambda item: (item.priority, item.path))[:12]

    def _document_title(self, path: Path, text: str) -> str:
        for line in text.splitlines():
            stripped = line.strip("# ").strip()
            if stripped:
                return stripped[:120]
        return path.name

    def _source_summaries(self, repo: Path, files: list[Path]) -> list[SourceSummary]:
        summaries: list[SourceSummary] = []
        for path in files:
            relative = str(path.relative_to(repo))
            kind, priority = self._classify_source(relative, path)
            if not kind:
                continue
            evidence = self._evidence_lines(path, kind)
            summaries.append(
                SourceSummary(
                    path=relative,
                    kind=kind,
                    summary=self._source_summary(relative, kind, evidence),
                    evidence=evidence,
                    priority=priority,
                )
            )
        return sorted(summaries, key=lambda item: (item.priority, item.path))[:40]

    def _classify_source(self, relative: str, path: Path) -> tuple[str | None, int]:
        lowered = relative.lower()
        name = path.name.lower()
        if name in {"main.rs", "lib.rs", "main.py", "app.py", "main.dart"}:
            return "main service entrypoint", 10
        if name in {"package.json", "cargo.toml", "pubspec.yaml", "pyproject.toml"}:
            return "dependency manifest", 12
        if ".github/workflows/" in lowered:
            return "CI workflow", 14
        if path.suffix == ".tf":
            return "Terraform module layout", 16
        if name in {"docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"}:
            return "Docker Compose topology", 18
        if any(token in lowered for token in ("router", "routes", "route")):
            return "router composition", 20
        if any(token in lowered for token in ("auth", "middleware", "session", "jwt")):
            return "middleware/auth boundary", 22
        if path.suffix in {".rs", ".py", ".ts", ".tsx", ".dart"} and path.stat().st_size > 20_000:
            return "large handler or module", 32
        return None, 100

    def _evidence_lines(self, path: Path, kind: str) -> list[str]:
        if kind == "dependency manifest":
            return [
                f"Manifest file `{path.name}` declares project dependencies or "
                "workspace metadata."
            ]
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            return []
        patterns = {
            "main service entrypoint": r"\b(main|Router|FastAPI|runApp|tokio::main)\b",
            "router composition": r"\b(route|Router|nest|merge|get|post|put|delete)\b",
            "middleware/auth boundary": r"\b(auth|authorize|middleware|jwt|token|session)\b",
            "CI workflow": r"\b(name:|on:|jobs:|steps:|uses:|run:)\b",
            "Terraform module layout": r"\b(module|resource|provider|variable|output)\b",
            "Docker Compose topology": r"\b(services:|image:|build:|ports:|environment:)\b",
            "dependency manifest": r"\b(dependencies|devDependencies|workspace|flutter|project)\b",
        }
        regex = re.compile(patterns.get(kind, r"\S"), re.IGNORECASE)
        evidence: list[str] = []
        for index, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped and regex.search(stripped):
                evidence.append(f"L{index}: {stripped[:180]}")
            if len(evidence) >= 5:
                break
        if not evidence:
            evidence = [f"L1: {line.strip()[:180]}" for line in lines[:2] if line.strip()]
        return evidence

    def _source_summary(self, relative: str, kind: str, evidence: list[str]) -> str:
        if evidence:
            return f"{kind} identified from `{relative}` with {len(evidence)} evidence line(s)."
        return f"{kind} identified from `{relative}` by path/name."

    def _briefing(
        self,
        repo: Path,
        files: list[Path],
        stack: list[str],
        frameworks: list[str],
        guidance: list[GuidanceInsight],
        source_summaries: list[SourceSummary],
    ) -> BriefingInsight:
        purpose_source = next(
            (item.summary for item in guidance if item.path == "README.md"),
            None,
        )
        product_purpose = purpose_source or "No README or product overview was found."
        top_dirs = sorted(
            {
                path.relative_to(repo).parts[0]
                for path in files
                if len(path.relative_to(repo).parts) > 1
            }
        )
        structure = (
            f"Top-level areas: {', '.join(top_dirs[:12])}."
            if top_dirs
            else "Single-area repository or shallow project layout."
        )
        runtime = (
            ", ".join(item.path for item in source_summaries[:8])
            or "No runtime entrypoints detected."
        )
        local_dev = self._local_dev_summary(files)
        ci = self._ci_summary(repo, files)
        tradeoffs = self._tradeoff_summary(guidance)
        scaffold = self._scaffold_summary(repo, files)
        invariants = (
            "Guidance emphasizes: "
            + "; ".join(
                item.summary
                for item in guidance
                if item.path in {"AGENTS.md", "CLAUDE.md"}
            )[:500]
            if any(item.path in {"AGENTS.md", "CLAUDE.md"} for item in guidance)
            else "No explicit architecture invariants detected in guidance docs."
        )
        return BriefingInsight(
            product_purpose=product_purpose,
            monorepo_structure=structure,
            main_runtime_components=(
                f"{', '.join(stack or frameworks) or 'Unknown stack'} via {runtime}"
            ),
            architectural_invariants=invariants,
            shipped_state=scaffold,
            local_development=local_dev,
            ci_expectations=ci,
            tradeoffs=tradeoffs,
        )

    def _local_dev_summary(self, files: list[Path]) -> str:
        names = {path.name for path in files}
        signals: list[str] = []
        if "pyproject.toml" in names:
            signals.append("Python project metadata")
        if "package.json" in names:
            signals.append("Node package scripts/dependencies")
        if "Cargo.toml" in names:
            signals.append("Cargo build/test workflow")
        if "pubspec.yaml" in names:
            signals.append("Flutter pub workflow")
        if "docker-compose.yml" in names or "docker-compose.yaml" in names:
            signals.append("Docker Compose local services")
        return ", ".join(signals) if signals else "No local setup manifest detected."

    def _ci_summary(self, repo: Path, files: list[Path]) -> str:
        workflows = [
            str(path.relative_to(repo))
            for path in files
            if ".github/workflows/" in path.as_posix()
        ]
        if workflows:
            return f"GitHub Actions workflows: {', '.join(workflows[:8])}."
        return "No GitHub Actions workflow detected."

    def _tradeoff_summary(self, guidance: list[GuidanceInsight]) -> str:
        tradeoff_docs = [
            item.summary
            for item in guidance
            if re.search(
                r"\b(tradeoff|deferred|not implemented|future|intentional)\b",
                item.summary,
                re.I,
            )
        ]
        return "; ".join(tradeoff_docs[:3]) if tradeoff_docs else "No explicit tradeoffs found."

    def _scaffold_summary(self, repo: Path, files: list[Path]) -> str:
        markers: list[str] = []
        for path in files:
            if path.suffix not in IMPORTANT_SUFFIXES:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")[:8_000]
            except OSError:
                continue
            if re.search(r"\b(stub|scaffold|placeholder|not implemented|TODO)\b", text, re.I):
                markers.append(str(path.relative_to(repo)))
            if len(markers) >= 8:
                break
        return (
            f"Potential scaffold/deferred markers in: {', '.join(markers)}."
            if markers
            else "No obvious scaffold or placeholder markers detected."
        )

    def _summarize_text(self, text: str, max_chars: int) -> str:
        lines = []
        seen: set[str] = set()
        for line in text.splitlines():
            stripped = re.sub(r"\s+", " ", line.strip(" #-"))
            if stripped:
                sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", stripped)]
                for sentence in sentences:
                    if sentence and sentence not in seen:
                        seen.add(sentence)
                        lines.append(sentence)
        summary = " ".join(lines)
        if len(summary) <= max_chars:
            return summary
        return summary[: max_chars - 1].rstrip() + "..."
