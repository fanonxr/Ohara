from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class FileInsight:
    path: Path
    relative_path: str
    reason: str
    size_bytes: int
    priority: int


@dataclass(frozen=True)
class TodoInsight:
    path: str
    line: int
    text: str


@dataclass(frozen=True)
class RiskInsight:
    kind: str
    path: str
    line: int
    description: str


@dataclass(frozen=True)
class GuidanceInsight:
    path: str
    title: str
    summary: str
    priority: int


@dataclass(frozen=True)
class BriefingInsight:
    product_purpose: str = "Not enough evidence in repository guidance."
    monorepo_structure: str = "No monorepo layout detected."
    main_runtime_components: str = "No runtime components detected."
    architectural_invariants: str = "No explicit invariants detected."
    shipped_state: str = "No shipped-versus-scaffold signal detected."
    local_development: str = "No local development workflow detected."
    ci_expectations: str = "No CI or deployment signal detected."
    tradeoffs: str = "No intentional tradeoffs or deferred work detected."


@dataclass(frozen=True)
class SourceSummary:
    path: str
    kind: str
    summary: str
    evidence: list[str] = field(default_factory=list)
    priority: int = 100


@dataclass(frozen=True)
class ExcludedPath:
    path: str
    reason: str


@dataclass(frozen=True)
class RepositorySummary:
    path: Path
    name: str
    frameworks: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    stack: list[str] = field(default_factory=list)
    important_files: list[FileInsight] = field(default_factory=list)
    todos: list[TodoInsight] = field(default_factory=list)
    risks: list[RiskInsight] = field(default_factory=list)
    directory_tree: list[str] = field(default_factory=list)
    guidance: list[GuidanceInsight] = field(default_factory=list)
    briefing: BriefingInsight = field(default_factory=BriefingInsight)
    source_summaries: list[SourceSummary] = field(default_factory=list)
    excluded_paths: list[ExcludedPath] = field(default_factory=list)


@dataclass(frozen=True)
class ScanResult:
    repositories: list[RepositorySummary]
