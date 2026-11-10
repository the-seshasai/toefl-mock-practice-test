import json
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

from app.llm.base import LLMProvider
from app.llm.errors import LLMConfigError, LLMError
from app.llm.throttle import Throttle

Runner = Callable[..., subprocess.CompletedProcess[str]]


class ClaudeCodeProvider(LLMProvider):
    """Local provider: shells out to headless Claude Code (`claude -p`) using the user's own login.

    Runs with no tools, no session persistence, and from a neutral work_dir so no project
    CLAUDE.md or settings leak into the prompt.
    """

    name = "claude_code"

    def __init__(self, cli_path: str, model: str, *, work_dir: Path, throttle: Throttle,
                 max_retries: int = 2, timeout: float = 120.0, runner: Runner = subprocess.run) -> None:
        self._cli = cli_path
        self._model = model
        self._work_dir = work_dir
        self._throttle = throttle
        self._max_retries = max_retries
        self._timeout = timeout
        self._run = runner

    def complete(self, prompt: str, *, system: str | None = None, json_mode: bool = False,
                 temperature: float = 0.8) -> str:  # temperature is not configurable via the CLI
        system = system or "You are a precise assistant."
        if json_mode:
            system += "\nRespond with ONLY a single valid JSON value, no prose or code fences."
        cmd = [self._cli, "-p", "--output-format", "json", "--tools", "", "--no-session-persistence",
               "--setting-sources", "", "--system-prompt", system]
        if self._model:
            cmd += ["--model", self._model]
        last = ""
        for attempt in range(self._max_retries + 1):
            self._throttle.wait()
            try:
                proc = self._run(cmd, input=prompt, capture_output=True, text=True,
                                 timeout=self._timeout, cwd=self._work_dir)
            except FileNotFoundError as exc:
                raise LLMConfigError(f"Claude Code CLI not found at '{self._cli}'") from exc
            except subprocess.TimeoutExpired:
                last = "timed out"
            else:
                out = _parse(proc.stdout)
                if proc.returncode == 0 and out is not None and not out.get("is_error") and out.get("result"):
                    return str(out["result"])
                last = (out or {}).get("result") or proc.stderr.strip()[:300] or f"exit {proc.returncode}"
            if attempt < self._max_retries:
                time.sleep(2.0 ** attempt * 2)
        raise LLMError(f"claude code failed: {last}")


def _parse(stdout: str) -> dict | None:
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None
