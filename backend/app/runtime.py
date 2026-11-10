"""Process-wide seams: which LLM to use and how background work runs (both swappable in tests)."""
import logging
import threading
from collections.abc import Callable
from typing import Any

from app.audio.stt import Transcriber, WhisperTranscriber
from app.audio.tts import PiperSynthesizer, Synthesizer
from app.config import settings
from app.llm import LLMProvider, get_provider

log = logging.getLogger(__name__)

_llm_factory: Callable[[], LLMProvider] = get_provider


def get_llm() -> LLMProvider:
    return _llm_factory()


def set_llm_factory(factory: Callable[[], LLMProvider] | None) -> None:
    global _llm_factory
    _llm_factory = factory or get_provider


def _thread_runner(fn: Callable[..., None], *args: Any) -> None:
    def target() -> None:
        try:
            fn(*args)
        except Exception:
            log.exception("background job %s failed", getattr(fn, "__name__", fn))

    threading.Thread(target=target, daemon=True).start()


_runner: Callable[..., None] = _thread_runner


def run_background(fn: Callable[..., None], *args: Any) -> None:
    _runner(fn, *args)


def set_background_runner(runner: Callable[..., None] | None) -> None:
    global _runner
    _runner = runner or _thread_runner


_tts: Synthesizer | None = None
_tts_factory: Callable[[], Synthesizer] | None = None


def get_tts() -> Synthesizer:
    """One shared synthesizer per process (it caches the loaded voice model)."""
    global _tts
    if _tts is None:
        _tts = _tts_factory() if _tts_factory else PiperSynthesizer(settings.piper_voice_dir)
    return _tts


def set_tts_factory(factory: Callable[[], Synthesizer] | None) -> None:
    global _tts, _tts_factory
    _tts_factory = factory
    _tts = None


_stt: Transcriber | None = None
_stt_factory: Callable[[], Transcriber] | None = None


def get_stt() -> Transcriber:
    global _stt
    if _stt is None:
        _stt = _stt_factory() if _stt_factory else WhisperTranscriber(settings.whisper_dir / settings.whisper_model)
    return _stt


def set_stt_factory(factory: Callable[[], Transcriber] | None) -> None:
    global _stt, _stt_factory
    _stt_factory = factory
    _stt = None
