from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from ohara.automation.base import BrowserReviewProvider, ReviewRequest
from ohara.automation.chatgpt import ChatGPTPlaywrightCliProvider
from ohara.context.builder import ContextBuilder
from ohara.context.scanner import RepositoryScanner
from ohara.parsers.json_parser import ReviewJsonParser, ReviewParseError
from ohara.schemas.review import ReviewOutput
from ohara.storage.filesystem import FileSystemStorage
from ohara.templates.registry import get_template


@dataclass(frozen=True)
class ReviewRunResult:
    run_path: Path
    context_markdown: str
    raw_response: str | None
    parsed: ReviewOutput | None


class ReviewRunner:
    def __init__(
        self,
        output_dir: Path = Path(".ohara/reviews"),
        provider: BrowserReviewProvider | None = None,
    ) -> None:
        self.output_dir = output_dir
        self.provider = provider
        self.scanner = RepositoryScanner()
        self.builder = ContextBuilder()
        self.parser = ReviewJsonParser()
        self.storage = FileSystemStorage(output_dir)

    def run(
        self,
        template_name: str,
        repositories: list[Path],
        dry_run: bool = False,
        use_browser: bool = True,
    ) -> ReviewRunResult:
        template = get_template(template_name)
        self.scanner.review_mode = template.name
        scan = self.scanner.scan(repositories)
        context_markdown = self.builder.build(scan, template_name=template.name)

        if dry_run or not use_browser:
            artifact = self.storage.save_context(
                template=template.name,
                context_markdown=context_markdown,
                logs=["browser disabled; generated context package only"],
            )
            return ReviewRunResult(
                run_path=artifact.path,
                context_markdown=context_markdown,
                raw_response=None,
                parsed=None,
            )

        context_artifact = self.storage.save_context(
            template=template.name,
            context_markdown=context_markdown,
            logs=["context generated"],
        )
        prompt = template.render_prompt("", context_delivery="uploaded")
        request = ReviewRequest(
            template_name=template.name,
            prompt=prompt,
            context_markdown=context_markdown,
            context_path=context_artifact.path / "context.md",
        )
        provider = self.provider or ChatGPTPlaywrightCliProvider()
        response = asyncio.run(provider.submit_review(request))
        logs = [
            f"model={response.model or 'unknown'}",
            *[f"{key}={value}" for key, value in response.metadata.items()],
        ]
        try:
            parsed = self.parser.parse(response.raw_text)
        except ReviewParseError as exc:
            self.storage.save_parse_failure(
                template=template.name,
                context_markdown=context_markdown,
                raw_response=response.raw_text,
                error=str(exc),
                logs=[*logs, "parse failed"],
                run_path=context_artifact.path,
            )
            raise
        artifact = self.storage.save_review(
            template=template.name,
            context_markdown=context_markdown,
            raw_response=response.raw_text,
            parsed=parsed,
            logs=logs,
            run_path=context_artifact.path,
        )
        return ReviewRunResult(
            run_path=artifact.path,
            context_markdown=context_markdown,
            raw_response=response.raw_text,
            parsed=parsed,
        )
