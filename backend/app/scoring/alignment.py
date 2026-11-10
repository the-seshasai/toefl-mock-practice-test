"""Word-level alignment of a spoken transcript to a target sentence."""
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from app.audio.stt import Transcript

_NUMBER_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
                 "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]
RUBRIC_DIR = Path(__file__).parent / "rubrics"
REPEAT_RUBRIC = "speaking_repeat.v1.txt"
LONG_PAUSE_SECONDS = 0.8
LOW_CONFIDENCE = 0.5


def tokens(text: str) -> list[str]:
    text = text.lower().replace("’", "'")
    out = []
    for tok in re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text):
        out.append(_NUMBER_WORDS[int(tok)] if tok.isdigit() and int(tok) < len(_NUMBER_WORDS) else tok)
    return out


def load_thresholds() -> list[tuple[float, int]]:
    """Read '(min accuracy) (score)' lines from the versioned rubric file."""
    rows: list[tuple[float, int]] = []
    for line in (RUBRIC_DIR / REPEAT_RUBRIC).read_text().splitlines():
        m = re.fullmatch(r"(\d\.\d+)\s+(\d)", line.strip())
        if m:
            rows.append((float(m.group(1)), int(m.group(2))))
    return sorted(rows, reverse=True)


def score_from_accuracy(accuracy: float) -> int:
    for minimum, score in load_thresholds():
        if accuracy >= minimum:
            return score
    return 0


def align(target: str, heard: str) -> dict[str, Any]:
    t, h = tokens(target), tokens(heard)
    sm = SequenceMatcher(None, t, h, autojunk=False)
    matched = sum(block.size for block in sm.get_matching_blocks())
    accuracy = matched / max(len(t), len(h), 1) if h else 0.0
    differences: list[dict[str, str]] = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "delete":
            differences.append({"type": "missing", "target": " ".join(t[i1:i2]), "heard": ""})
        elif op == "insert":
            differences.append({"type": "extra", "target": "", "heard": " ".join(h[j1:j2])})
        elif op == "replace":
            differences.append({"type": "changed", "target": " ".join(t[i1:i2]), "heard": " ".join(h[j1:j2])})
    return {"accuracy": round(accuracy, 3), "differences": differences, "target_words": len(t), "heard_words": len(h)}


def delivery_stats(tr: Transcript) -> dict[str, Any]:
    """Delivery measures from word timings: speech rate, long pauses, recognizer confidence."""
    if not tr.words:
        return {"duration_s": round(tr.duration, 1), "words": 0, "wpm": 0, "long_pauses": 0, "avg_confidence": 0.0, "unclear_words": []}
    speaking = max(tr.words[-1].end - tr.words[0].start, 0.1)
    pauses = sum(1 for a, b in zip(tr.words, tr.words[1:], strict=False) if b.start - a.end >= LONG_PAUSE_SECONDS)
    return {
        "duration_s": round(tr.duration, 1), "words": len(tr.words), "wpm": round(len(tr.words) / speaking * 60),
        "long_pauses": pauses, "avg_confidence": round(sum(w.prob for w in tr.words) / len(tr.words), 2),
        "unclear_words": [w.word for w in tr.words if w.prob < LOW_CONFIDENCE][:6],
    }
