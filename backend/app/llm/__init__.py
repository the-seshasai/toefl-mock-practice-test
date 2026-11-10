from app.config import Settings, settings
from app.llm.base import LLMProvider
from app.llm.claude_code import ClaudeCodeProvider
from app.llm.throttle import Throttle

_throttle: Throttle | None = None


def build_provider(cfg: Settings, throttle: Throttle | None = None) -> LLMProvider:
    """The only provider is local Claude Code (`claude -p`). One shared throttle per process."""
    global _throttle
    if throttle is None:
        _throttle = _throttle or Throttle(cfg.llm_min_interval_seconds)
        throttle = _throttle
    work_dir = cfg.data_dir / "claude_workdir"
    work_dir.mkdir(parents=True, exist_ok=True)
    return ClaudeCodeProvider(cfg.claude_path, cfg.claude_model, work_dir=work_dir, throttle=throttle,
                              max_retries=cfg.llm_max_retries, timeout=cfg.llm_timeout_seconds)


def get_provider() -> LLMProvider:
    return build_provider(settings)


__all__ = ["LLMProvider", "build_provider", "get_provider"]
