from __future__ import annotations

import json
import re

from pydantic import ValidationError

from ohara.schemas.review import ReviewOutput


class ReviewParseError(ValueError):
    """Raised when a model response cannot be parsed into strict review JSON."""


class ReviewJsonParser:
    def parse(self, raw_text: str) -> ReviewOutput:
        errors: list[str] = []
        for json_text in self._json_candidates(raw_text):
            repaired = self._repair(json_text)
            try:
                payload = json.loads(repaired)
            except json.JSONDecodeError as exc:
                errors.append(f"invalid JSON candidate: {exc}")
                continue
            try:
                return ReviewOutput.model_validate(payload)
            except ValidationError as exc:
                errors.append(f"schema validation failed: {exc}")
                continue
        if errors:
            raise ReviewParseError(
                "Response did not contain valid review JSON. "
                + " Last parser error: "
                + errors[-1]
            )
        raise ReviewParseError("Response did not contain a JSON object.")

    def _extract_json(self, raw_text: str) -> str:
        try:
            return next(self._json_candidates(raw_text))
        except StopIteration as exc:
            raise ReviewParseError("Response did not contain a JSON object.") from exc

    def _json_candidates(self, raw_text: str):
        for fenced in re.finditer(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL):
            yield fenced.group(1)
        yield from self._balanced_json_objects(raw_text)

    def _balanced_json_objects(self, raw_text: str):
        for start, char in enumerate(raw_text):
            if char != "{":
                continue
            depth = 0
            in_string = False
            escaped = False
            for index in range(start, len(raw_text)):
                current = raw_text[index]
                if in_string:
                    if escaped:
                        escaped = False
                    elif current == "\\":
                        escaped = True
                    elif current == '"':
                        in_string = False
                    continue
                if current == '"':
                    in_string = True
                elif current == "{":
                    depth += 1
                elif current == "}":
                    depth -= 1
                    if depth == 0:
                        yield raw_text[start : index + 1]
                        break

    def _repair(self, json_text: str) -> str:
        return re.sub(r",(\s*[}\]])", r"\1", json_text.strip())
