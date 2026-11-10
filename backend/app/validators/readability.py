"""Readability measures used to keep difficulty levels distinct."""
import re


def syllables(word: str) -> int:
    word = re.sub(r"[^a-z]", "", word.lower())
    if not word:
        return 0
    groups = len(re.findall(r"[aeiouy]+", word))
    if word.endswith("e") and not word.endswith(("le", "ee")) and groups > 1:
        groups -= 1
    return max(groups, 1)


def fk_grade(text: str) -> float:
    """Flesch-Kincaid grade level (ETS cites ~7.4-10.5 for medium and 10.5+ for high-difficulty reading texts)."""
    sentences = max(len(re.findall(r"[.!?]+(?:\s|$)", text)), 1)
    words = re.findall(r"[A-Za-z']+", text)
    if not words:
        return 0.0
    return 0.39 * len(words) / sentences + 11.8 * sum(syllables(w) for w in words) / len(words) - 15.59
