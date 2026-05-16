from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from ohara.automation.base import ReviewRequest, ReviewResponse

ASSISTANT_MESSAGE_SEPARATOR = "---OHARA_ASSISTANT_MESSAGE---"
UI_NOISE_LINES = {
    "ChatGPT",
    "Copy code",
    "Upgrade plan",
    "ChatGPT can make mistakes.",
}


class PlaywrightCliRunner(Protocol):
    async def run(self, args: list[str]) -> str:
        """Run a playwright-cli command and return stdout."""


@dataclass
class SubprocessPlaywrightCliRunner:
    async def run(self, args: list[str]) -> str:
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(
                f"playwright-cli command failed ({process.returncode}): "
                f"{stderr.decode(errors='replace').strip()}"
            )
        return stdout.decode(errors="replace").strip()


@dataclass
class ChatGPTPlaywrightCliProvider:
    """ChatGPT provider backed by the Microsoft `@playwright/cli` command.

    This intentionally shells out to `playwright-cli` instead of using the Python
    Playwright API or Playwright MCP. The CLI keeps browser state in named
    sessions and is token-efficient for coding agents.
    """

    command: tuple[str, ...] = ("playwright-cli",)
    session: str = "ohara-chatgpt"
    profile_dir: Path = Path(".ohara/playwright-cli-profile")
    headed: bool = True
    chatgpt_url: str = "https://chatgpt.com/"
    completion_idle_seconds: float = 4.0
    runner: PlaywrightCliRunner | None = None
    script_dir: Path = Path(".ohara/playwright-cli-scripts")

    async def submit_review(self, request: ReviewRequest) -> ReviewResponse:
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.script_dir.mkdir(parents=True, exist_ok=True)
        runner = self.runner or SubprocessPlaywrightCliRunner()

        await runner.run(self._open_command())
        script_path = self._write_submit_script(request)
        raw_text = await runner.run(
            [
                *self.command,
                f"-s={self.session}",
                "--raw",
                "run-code",
                f"--filename={script_path}",
            ]
        )
        raw_text = extract_assistant_response_text(raw_text)
        return ReviewResponse(
            raw_text=raw_text,
            model=request.model,
            metadata={"provider": "chatgpt-playwright-cli", "session": self.session},
        )

    def _open_command(self) -> list[str]:
        command = [
            *self.command,
            f"-s={self.session}",
            "open",
            self.chatgpt_url,
            "--persistent",
            f"--profile={self.profile_dir}",
        ]
        if self.headed:
            command.append("--headed")
        return command

    def _write_submit_script(self, request: ReviewRequest) -> Path:
        script_path = self.script_dir / f"submit-review-{uuid4().hex}.js"
        prompt = request.prompt
        inline_context = self._inline_context_prompt(request.context_markdown, request.prompt)
        context_path = str(request.context_path) if request.context_path else None

        script_path.write_text(
            self._script_source(
                prompt=prompt,
                inline_context=inline_context,
                context_path=context_path,
            ),
            encoding="utf-8",
        )
        return script_path

    def _script_source(
        self,
        prompt: str,
        inline_context: str,
        context_path: str | None,
    ) -> str:
        return f"""async page => {{
  const prompt = {json.dumps(prompt)};
  const inlineContext = {json.dumps(inline_context)};
  const contextPath = {json.dumps(context_path)};

  let textToSubmit = prompt;
  if (contextPath) {{
    const fileInputs = page.locator('input[type="file"]');
    try {{
      if (await fileInputs.count()) {{
        await fileInputs.first().setInputFiles(contextPath);
        textToSubmit = [
          'The uploaded markdown file contains the repository context.',
          'Review only that context and cite evidence from it.\\n\\n',
          prompt
        ].join(' ');
      }} else {{
        textToSubmit = inlineContext;
      }}
    }} catch (error) {{
      textToSubmit = inlineContext;
    }}
  }} else {{
    textToSubmit = inlineContext;
  }}

  const assistant = page.locator('[data-message-author-role="assistant"]');
  const beforeCount = await assistant.count();

  function failSubmit(message) {{
    throw new Error(`OHARA_SUBMIT_FAILED: ${{message}}`);
  }}

  function normalizePrompt(value) {{
    return (value || '').replace(/\\r\\n/g, '\\n').replace(/\\u00a0/g, ' ').trim();
  }}

  const editor = page.locator('textarea, [contenteditable="true"]').last();
  await editor.waitFor({{ state: 'visible', timeout: 30000 }});

  async function readPromptText() {{
    return await editor.evaluate(element => {{
      if ('value' in element) {{
        return element.value || '';
      }}
      return element.innerText || element.textContent || '';
    }});
  }}

  async function promptTextMatches(expected) {{
    const expectedText = normalizePrompt(expected);
    const actualText = normalizePrompt(await readPromptText());
    const head = expectedText.slice(0, Math.min(80, expectedText.length));
    const tail = expectedText.slice(Math.max(0, expectedText.length - 80));
    return (
      actualText.length >= Math.floor(expectedText.length * 0.98) &&
      actualText.startsWith(head) &&
      actualText.includes(tail)
    );
  }}

  async function waitForPromptText(expected) {{
    const deadline = Date.now() + 15000;
    while (Date.now() < deadline) {{
      if (await promptTextMatches(expected)) {{
        return;
      }}
      await page.waitForTimeout(250);
    }}
    const actualLength = normalizePrompt(await readPromptText()).length;
    failSubmit(
      `prompt text was not fully inserted: expected ${{normalizePrompt(expected).length}} ` +
      `chars, found ${{actualLength}}`
    );
  }}

  await editor.click();
  try {{
    await editor.fill(textToSubmit);
  }} catch (error) {{
    // Fall back below; ChatGPT has alternated between textarea and rich editor internals.
  }}
  if (!(await promptTextMatches(textToSubmit))) {{
    await editor.click();
    await page.keyboard.press('ControlOrMeta+A');
    await page.keyboard.press('Backspace');
    await page.keyboard.insertText(textToSubmit);
  }}
  await waitForPromptText(textToSubmit);

  const sendButton = page
    .locator([
      'button[aria-label="Send prompt"]',
      'button[aria-label="Send message"]',
      'button[data-testid="send-button"]'
    ].join(', '))
    .last();
  const sendDeadline = Date.now() + 30000;
  while (Date.now() < sendDeadline) {{
    if (await sendButton.count()) {{
      const disabled = await sendButton.evaluate(element => {{
        return Boolean(element.disabled) || element.getAttribute('aria-disabled') === 'true';
      }});
      if (!disabled) {{
        break;
      }}
    }}
    await page.waitForTimeout(500);
  }}
  if (!(await sendButton.count())) {{
    failSubmit('send button was not found');
  }}
  const sendDisabled = await sendButton.evaluate(element => {{
    return Boolean(element.disabled) || element.getAttribute('aria-disabled') === 'true';
  }});
  if (sendDisabled) {{
    failSubmit('send button stayed disabled after prompt insertion');
  }}
  await sendButton.click();

  let stableText = '';
  let stableIterations = 0;
  let responseStarted = false;
  const deadline = Date.now() + 180000;
  while (Date.now() < deadline) {{
    await page.waitForTimeout({int(self.completion_idle_seconds * 1000)});
    const count = await assistant.count();
    if (count <= beforeCount) {{
      continue;
    }}
    responseStarted = true;
    const currentText = await assistant.nth(count - 1).innerText();
    const stopControls = await page
      .locator('button[aria-label*="Stop"], button:has-text("Stop")')
      .count();
    if (currentText && currentText === stableText && stopControls === 0) {{
      stableIterations += 1;
    }} else {{
      stableIterations = 0;
      stableText = currentText;
    }}
    if (stableIterations >= 1) {{
      break;
    }}
  }}
  if (!responseStarted) {{
    failSubmit('no assistant response started');
  }}

  const count = await assistant.count();
  const messages = [];
  for (let index = 0; index < count; index += 1) {{
    messages.push(await assistant.nth(index).innerText());
  }}
  return messages.join('\\n{ASSISTANT_MESSAGE_SEPARATOR}\\n');
}}"""

    def _inline_context_prompt(self, context_markdown: str, prompt: str) -> str:
        return (
            "The repository context is included below. Review only this context and cite "
            "evidence from it.\n\n"
            f"{prompt}\n\n## Repository Context\n{context_markdown}"
        )


def extract_assistant_response_text(raw_text: str) -> str:
    """Return the last assistant message and strip common ChatGPT UI chrome."""

    segments = [segment.strip() for segment in raw_text.split(ASSISTANT_MESSAGE_SEPARATOR)]
    text = next((segment for segment in reversed(segments) if segment), raw_text)
    cleaned_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped in UI_NOISE_LINES:
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


ChatGPTPlaywrightProvider = ChatGPTPlaywrightCliProvider
