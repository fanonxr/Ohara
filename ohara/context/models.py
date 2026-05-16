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


@dataclass(frozen=True)
class ScanResult:
    repositories: list[RepositorySummary]
