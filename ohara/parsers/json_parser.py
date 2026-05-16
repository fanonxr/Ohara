from __future__ import annotations

import json
import re

from pydantic import ValidationError

from ohara.schemas.review import ReviewOutput


class ReviewParseError(ValueError):
    """Raised when a model response cannot be parsed into strict review JSON."""


class ReviewJsonParser:
    def parse(self, raw_text: str) -> ReviewOutput:
        json_text = self._extract_json(raw_text)
        repaired = self._repair(json_text)
        try:
            payload = json.loads(repaired)
        except json.JSONDecodeError as exc:
            raise ReviewParseError(f"Response did not contain valid JSON: {exc}") from exc
        try:
            return ReviewOutput.model_validate(payload)
        except ValidationError as exc:
            raise ReviewParseError(f"Response JSON failed schema validation: {exc}") from exc

    def _extract_json(self, raw_text: str) -> str:
        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
        if fenced:
            return fenced.group(1)
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ReviewParseError("Response did not contain a JSON object.")
        return raw_text[start : end + 1]

    def _repair(self, json_text: str) -> str:
        return re.sub(r",(\s*[}\]])", r"\1", json_text.strip())
