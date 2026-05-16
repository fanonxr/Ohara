from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from ohara.automation.base import ReviewRequest, ReviewResponse


@dataclass
class ChatGPTPlaywrightProvider:
    """Playwright-backed ChatGPT provider.

    The provider intentionally keeps selectors conservative and configurable. It is
    a V1 integration boundary, not a guarantee against future ChatGPT UI changes.
    """

    user_data_dir: Path = Path(".ohara/browser-profile")
    headless: bool = False
    chatgpt_url: str = "https://chatgpt.com/"
    completion_idle_seconds: float = 4.0

    async def submit_review(self, request: ReviewRequest) -> ReviewResponse:
        try:
            from playwright.async_api import TimeoutError as PlaywrightTimeoutError
            from playwright.async_api import async_playwright
        except ImportError as exc:  # pragma: no cover - dependency is installed in normal use
            raise RuntimeError("Playwright is required for ChatGPT automation.") from exc

        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        async with async_playwright() as playwright:
            context = await playwright.chromium.launch_persistent_context(
                str(self.user_data_dir),
                headless=self.headless,
            )
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto(self.chatgpt_url, wait_until="domcontentloaded")

            prompt = request.prompt
            if request.context_path is not None:
                prompt = (
                    f"Use the uploaded markdown context file for the review.\n\n{request.prompt}"
                )
                file_input = page.locator("input[type='file']").first
                try:
                    await file_input.set_input_files(str(request.context_path), timeout=5000)
                except PlaywrightTimeoutError:
                    prompt = (
                        "The browser upload control was not found. "
                        "Inline context follows.\n\n"
                        f"{request.context_markdown}\n\n{request.prompt}"
                    )
            else:
                prompt = f"{request.context_markdown}\n\n{request.prompt}"

            editor = page.locator("textarea, [contenteditable='true']").last
            await editor.fill(prompt)
            await page.keyboard.press("Enter")
            await asyncio.sleep(self.completion_idle_seconds)

            response_nodes = page.locator("[data-message-author-role='assistant']")
            count = await response_nodes.count()
            raw_text = await response_nodes.nth(count - 1).inner_text() if count else ""
            await context.close()
            return ReviewResponse(
                raw_text=raw_text,
                model=request.model,
                metadata={"provider": "chatgpt-playwright"},
            )
