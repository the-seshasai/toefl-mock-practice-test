"""Piper voice catalogue. Piper has no Australian English voice, so accents are US and UK (D-17)."""
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Voice:
    name: str
    gender: str
    accent: str


VOICES: tuple[Voice, ...] = (
    Voice("en_US-ryan-medium", "male", "US"),
    Voice("en_US-amy-medium", "female", "US"),
    Voice("en_GB-alba-medium", "female", "UK"),
    Voice("en_GB-northern_english_male-medium", "male", "UK"),
)
BY_NAME = {v.name: v for v in VOICES}


class AudioUnavailable(Exception):
    """No usable TTS voices (Piper voice files missing)."""


def assign_script_voices(script: list[dict], available: list[str]) -> None:
    """Give every speaker in the script a voice (by gender, distinct per speaker); mutates the lines in place."""
    speakers: dict[str, str] = {}
    for line in script:
        speakers.setdefault(line["speaker"], line.get("gender", "female"))
    voices = dict(zip(speakers, pick_voices(list(speakers.values()), available), strict=True))
    for line in script:
        line["voice"] = voices[line["speaker"]]


def pick_voices(genders: list[str], available: list[str]) -> list[str]:
    """Choose one voice per speaker by gender; two speakers never share a voice when avoidable."""
    pool = [BY_NAME[n] for n in available if n in BY_NAME]
    if not pool:
        raise AudioUnavailable("No Piper voices found. Download them as described in the README (data/piper/).")
    chosen: list[str] = []
    for g in genders:
        options = [v for v in pool if v.gender == g and v.name not in chosen] or [v for v in pool if v.name not in chosen] or pool
        chosen.append(random.choice(options).name)
    return chosen
