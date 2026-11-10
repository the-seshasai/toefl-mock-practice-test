import json
import re
from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.llm.errors import LLMParseError

T = TypeVar("T", bound=BaseModel)

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def extract_json(text: str) -> Any:
    """Parse JSON from model output, tolerating markdown code fences."""
    return json.loads(_FENCE.sub("", text.strip()))


class LLMProvider(ABC):
    """The single interface every LLM call in the app goes through."""

    name: str

    @abstractmethod
    def complete(self, prompt: str, *, system: str | None = None, json_mode: bool = False,
                 temperature: float = 0.8) -> str:
        """Return the raw text completion. json_mode asks the provider for JSON output."""

    def generate_json(self, prompt: str, schema: type[T], *, system: str | None = None,
                      temperature: float = 0.8, max_attempts: int = 3) -> T:
        """Complete, parse and validate against a Pydantic model; re-ask with the error on failure."""
        current = prompt
        last_error = ""
        for _ in range(max_attempts):
            raw = self.complete(current, system=system, json_mode=True, temperature=temperature)
            try:
                return schema.model_validate(extract_json(raw))
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = str(exc)[:500]
                current = (
                    f"{prompt}\n\nYour previous reply was invalid ({last_error}). "
                    "Reply again with ONLY valid JSON matching the requested structure."
                )
        raise LLMParseError(f"No valid output after {max_attempts} attempts: {last_error}")
