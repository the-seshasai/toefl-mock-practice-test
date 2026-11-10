import json

import pytest
from pydantic import BaseModel

from app.config import Settings
from app.llm import build_provider
from app.llm.base import extract_json
from app.llm.errors import LLMConfigError, LLMParseError
from app.llm.fake import FakeProvider
from app.llm.throttle import Throttle


class Quiz(BaseModel):
    question: str
    answer: int


def no_throttle() -> Throttle:
    return Throttle(0.0)


def test_extract_json_strips_fences() -> None:
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_generate_json_validates() -> None:
    llm = FakeProvider([{"question": "2+2?", "answer": 4}])
    assert llm.generate_json("q", Quiz).answer == 4
    assert llm.calls[0]["json_mode"] is True


def test_generate_json_retries_with_error_then_succeeds() -> None:
    llm = FakeProvider(["not json", {"question": "x", "answer": 1}])
    assert llm.generate_json("q", Quiz).question == "x"
    assert "previous reply was invalid" in llm.calls[1]["prompt"]


def test_generate_json_gives_up() -> None:
    llm = FakeProvider([{"question": "x"}])
    with pytest.raises(LLMParseError):
        llm.generate_json("q", Quiz, max_attempts=3)
    assert len(llm.calls) == 3


def test_throttle_spaces_calls() -> None:
    now = [0.0]
    slept: list[float] = []

    def sleep(d: float) -> None:
        slept.append(d)
        now[0] += d

    t = Throttle(4.0, clock=lambda: now[0], sleep=sleep)
    t.wait()
    t.wait()
    assert slept == [4.0]


def _cli(runner):
    from pathlib import Path

    from app.llm.claude_code import ClaudeCodeProvider

    return ClaudeCodeProvider("claude", "haiku", work_dir=Path("."), throttle=no_throttle(), max_retries=1, runner=runner)


def test_claude_code_builds_command_and_parses_result() -> None:
    import subprocess

    seen: dict = {}

    def runner(cmd, **kw):
        seen["cmd"], seen["input"] = cmd, kw["input"]
        return subprocess.CompletedProcess(cmd, 0, json.dumps({"result": '{"question": "q", "answer": 3}', "is_error": False}), "")

    out = _cli(runner).generate_json("hello", Quiz, system="sys")
    assert out.answer == 3 and seen["input"] == "hello"
    assert seen["cmd"][:2] == ["claude", "-p"] and "--tools" in seen["cmd"] and seen["cmd"][-2:] == ["--model", "haiku"]


def test_claude_code_retries_then_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess

    from app.llm.errors import LLMError

    monkeypatch.setattr("app.llm.claude_code.time.sleep", lambda _: None)
    calls = {"n": 0}

    def runner(cmd, **kw):
        calls["n"] += 1
        return subprocess.CompletedProcess(cmd, 1, "", "boom")

    with pytest.raises(LLMError, match="boom"):
        _cli(runner).complete("x")
    assert calls["n"] == 2


def test_claude_code_missing_binary() -> None:
    def runner(cmd, **kw):
        raise FileNotFoundError

    with pytest.raises(LLMConfigError):
        _cli(runner).complete("x")


def test_factory_builds_claude_code_provider(tmp_path) -> None:
    cfg = Settings(_env_file=None, data_dir=tmp_path, claude_model="haiku")
    p = build_provider(cfg, no_throttle())
    assert p.name == "claude_code"
