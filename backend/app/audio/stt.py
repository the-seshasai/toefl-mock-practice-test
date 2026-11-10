"""Speech-to-text: faster-whisper on CPU (int8). One model instance, freed after each scoring job (8 GB machine)."""
import gc
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


class SttError(Exception):
    """Transcription failed (undecodable audio, model error)."""


class SttUnavailable(SttError):
    """The Whisper model files are missing."""


@dataclass
class Word:
    word: str
    start: float
    end: float
    prob: float


@dataclass
class Transcript:
    text: str
    words: list[Word] = field(default_factory=list)
    duration: float = 0.0


class Transcriber(ABC):
    @abstractmethod
    def transcribe(self, path: Path) -> Transcript: ...

    def close(self) -> None:
        """Release model memory."""


class WhisperTranscriber(Transcriber):
    def __init__(self, model_dir: Path) -> None:
        self._dir = model_dir
        self._lock = threading.Lock()
        self._model = None

    def available(self) -> bool:
        return (self._dir / "model.bin").exists()

    def _load(self):
        if self._model is None:
            if not self.available():
                raise SttUnavailable(f"Whisper model not found in {self._dir}. Download it as described in the README.")
            from faster_whisper import WhisperModel  # lazy: ctranslate2 is heavy

            self._model = WhisperModel(str(self._dir), device="cpu", compute_type="int8", cpu_threads=4)
        return self._model

    def transcribe(self, path: Path) -> Transcript:
        with self._lock:
            model = self._load()
            try:
                segments, info = model.transcribe(
                    str(path), language="en", beam_size=1, vad_filter=True, word_timestamps=True,
                    condition_on_previous_text=False,
                )
                segs = list(segments)
            except Exception as exc:
                raise SttError(f"Could not transcribe {path.name}: {exc}") from exc
        words = [Word(w.word.strip(), float(w.start), float(w.end), float(w.probability)) for s in segs for w in (s.words or [])]
        return Transcript(text=" ".join(s.text.strip() for s in segs).strip(), words=words, duration=float(info.duration))

    def close(self) -> None:
        with self._lock:
            self._model = None
        gc.collect()
