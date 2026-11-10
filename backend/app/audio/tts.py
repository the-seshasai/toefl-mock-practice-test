"""Text-to-speech: Piper on CPU. Only one voice model is kept in memory at a time (8 GB machine)."""
import io
import threading
import wave
from abc import ABC, abstractmethod
from pathlib import Path

from app.audio.voices import VOICES, AudioUnavailable

SAMPLE_WIDTH = 2  # 16-bit mono


class Synthesizer(ABC):
    sample_rate: int = 22050

    @abstractmethod
    def available_voices(self) -> list[str]: ...

    @abstractmethod
    def synth(self, voice: str, text: str, length_scale: float) -> bytes:
        """Return raw 16-bit mono PCM at self.sample_rate."""


class PiperSynthesizer(Synthesizer):
    def __init__(self, voice_dir: Path) -> None:
        self._dir = voice_dir
        self._lock = threading.Lock()
        self._loaded_name: str | None = None
        self._loaded = None

    def available_voices(self) -> list[str]:
        return [v.name for v in VOICES if (self._dir / f"{v.name}.onnx").exists() and (self._dir / f"{v.name}.onnx.json").exists()]

    def _voice(self, name: str):
        if self._loaded_name != name:
            from piper import PiperVoice  # imported lazily: onnxruntime is heavy

            self._loaded = None  # free the previous model before loading the next
            path = self._dir / f"{name}.onnx"
            if not path.exists():
                raise AudioUnavailable(f"Piper voice file missing: {path}")
            self._loaded = PiperVoice.load(path)
            self._loaded_name = name
        return self._loaded

    def synth(self, voice: str, text: str, length_scale: float) -> bytes:
        from piper import SynthesisConfig

        with self._lock:  # one onnx session at a time
            v = self._voice(voice)
            buf = io.BytesIO()
            with wave.open(buf, "wb") as w:
                v.synthesize_wav(text, w, syn_config=SynthesisConfig(length_scale=length_scale))
            buf.seek(0)
            with wave.open(buf, "rb") as r:
                self.sample_rate = r.getframerate()
                return r.readframes(r.getnframes())
