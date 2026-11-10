import json
from collections.abc import Sequence
from typing import Any

from app.llm.base import LLMProvider


class FakeProvider(LLMProvider):
    """Scripted provider for tests: no network. Replies are returned in order (last one repeats)."""

    name = "fake"

    def __init__(self, replies: Sequence[Any]) -> None:
        self._replies = list(replies)
        self.calls: list[dict] = []

    def complete(self, prompt: str, *, system: str | None = None, json_mode: bool = False,
                 temperature: float = 0.8) -> str:
        self.calls.append({"prompt": prompt, "system": system, "json_mode": json_mode})
        reply = self._replies[min(len(self.calls) - 1, len(self._replies) - 1)]
        return reply if isinstance(reply, str) else json.dumps(reply)
