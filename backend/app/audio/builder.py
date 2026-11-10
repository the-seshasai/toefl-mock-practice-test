"""Turn a script (list of voiced lines) into one cached WAV file."""
import hashlib
import json
import wave
from pathlib import Path
from typing import Any

from app.audio.tts import SAMPLE_WIDTH, Synthesizer

PAUSE_SECONDS = 0.45  # between speakers


def script_key(script: list[dict[str, Any]], length_scale: float) -> str:
    raw = json.dumps([[s["voice"], s["text"]] for s in script] + [round(length_scale, 3)], sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


class AudioBuilder:
    def __init__(self, tts: Synthesizer, cache_dir: Path) -> None:
        self._tts = tts
        self._dir = cache_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, key: str) -> Path:
        return self._dir / f"{key}.wav"

    def build_many(self, jobs: list[tuple[list[dict[str, Any]], float]]) -> list[Path]:
        """Build every missing audio file, grouping synthesis by voice so each model loads once."""
        pending: list[tuple[str, list[dict[str, Any]], float]] = []
        for script, scale in jobs:
            key = script_key(script, scale)
            if not self.path_for(key).exists() and all(key != p[0] for p in pending):
                pending.append((key, script, scale))

        pcm: dict[tuple[str, str, float], bytes] = {}
        wanted = sorted({(s["voice"], s["text"], scale) for _, script, scale in pending for s in script})
        for voice, text, scale in wanted:  # sorted by voice first
            pcm[(voice, text, scale)] = self._tts.synth(voice, text, scale)

        for key, script, scale in pending:
            silence = b"\x00" * (int(self._tts.sample_rate * PAUSE_SECONDS) * SAMPLE_WIDTH)
            data = silence.join(pcm[(s["voice"], s["text"], scale)] for s in script)
            tmp = self.path_for(key).with_suffix(".tmp")
            with wave.open(str(tmp), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(SAMPLE_WIDTH)
                w.setframerate(self._tts.sample_rate)
                w.writeframes(data)
            tmp.replace(self.path_for(key))
        return [self.path_for(script_key(script, scale)) for script, scale in jobs]
