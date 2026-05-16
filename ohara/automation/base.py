from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class ReviewRequest:
    template_name: str
    prompt: str
    context_markdown: str
    context_path: Path | None = None
    model: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReviewResponse:
    raw_text: str
    model: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BrowserReviewProvider(Protocol):
    async def submit_review(self, request: ReviewRequest) -> ReviewResponse:
        """Submit a review request through a browser-backed AI provider."""
