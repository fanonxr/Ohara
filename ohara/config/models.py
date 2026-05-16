from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class ScannerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    include: list[str] | None = None
    exclude: list[str] = Field(default_factory=list)
    max_files: int = 400
    max_file_bytes: int = 512_000


class BrowserConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command: tuple[str, ...] = ("playwright-cli",)
    session: str = "ohara-chatgpt"
    profile_dir: Path = Path(".ohara/playwright-cli-profile")
    headed: bool = True
    chatgpt_url: str = "https://chatgpt.com/"
    model: str | None = None


class OharaConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    output_dir: Path = Path(".ohara/reviews")
    scanner: ScannerConfig = Field(default_factory=ScannerConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
