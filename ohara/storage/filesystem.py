from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from ohara.schemas.review import ReviewOutput


@dataclass(frozen=True)
class StoredRun:
    path: Path


class FileSystemStorage:
    def __init__(self, root: Path) -> None:
        self.root = root

    def save_context(
        self,
        template: str,
        context_markdown: str,
        logs: list[str] | None = None,
    ) -> StoredRun:
        run_path = self._new_run_path(template)
        run_path.mkdir(parents=True, exist_ok=False)
        self._write_common(run_path, template, context_markdown, logs or [])
        self._append_history(run_path, template, parsed=False)
        return StoredRun(path=run_path)

    def save_review(
        self,
        template: str,
        context_markdown: str,
        raw_response: str,
        parsed: ReviewOutput,
        logs: list[str] | None = None,
        run_path: Path | None = None,
    ) -> StoredRun:
        target = run_path or self._new_run_path(template)
        target.mkdir(parents=True, exist_ok=True)
        self._write_common(target, template, context_markdown, logs or [])
        (target / "raw-response.md").write_text(raw_response, encoding="utf-8")
        (target / "review.json").write_text(
            json.dumps(parsed.model_dump(mode="json"), indent=2) + "\n",
            encoding="utf-8",
        )
        self._append_history(target, template, parsed=True)
        return StoredRun(path=target)

    def save_parse_failure(
        self,
        template: str,
        context_markdown: str,
        raw_response: str,
        error: str,
        logs: list[str] | None = None,
        run_path: Path | None = None,
    ) -> StoredRun:
        target = run_path or self._new_run_path(template)
        target.mkdir(parents=True, exist_ok=True)
        self._write_common(target, template, context_markdown, logs or [])
        (target / "raw-response.md").write_text(raw_response, encoding="utf-8")
        (target / "parse-error.txt").write_text(error.rstrip() + "\n", encoding="utf-8")
        self._append_history(target, template, parsed=False)
        return StoredRun(path=target)

    def _write_common(
        self,
        run_path: Path,
        template: str,
        context_markdown: str,
        logs: list[str],
    ) -> None:
        (run_path / "context.md").write_text(context_markdown, encoding="utf-8")
        (run_path / "metadata.json").write_text(
            json.dumps(
                {
                    "template": template,
                    "created_at": datetime.now(UTC).isoformat(),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (run_path / "logs.txt").write_text("".join(f"{line}\n" for line in logs), encoding="utf-8")

    def _new_run_path(self, template: str) -> Path:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        return self.root / f"{timestamp}-{template}-{uuid4().hex[:8]}"

    def _append_history(self, run_path: Path, template: str, parsed: bool) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        entry = {
            "template": template,
            "run_path": str(run_path),
            "parsed": parsed,
            "created_at": datetime.now(UTC).isoformat(),
        }
        with (self.root / "history.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
