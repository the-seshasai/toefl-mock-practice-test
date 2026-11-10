import re
from itertools import pairwise

from app.difficulty import CompleteWordsParams
from app.schemas import CompleteWordsItem
from app.validators import in_range, word_count

MIN_BLANK_LETTERS = 3
_FIRST_SENTENCE_END = re.compile(r"[.!?](?:\s|$)")


def locate_blanks(text: str, blanks: list[str]) -> list[tuple[int, int]] | None:
    """Find each blank word in order as a whole word, skipping the (intact) first sentence. None if any is missing."""
    first = _FIRST_SENTENCE_END.search(text)
    cursor = first.end() if first else 0
    spans: list[tuple[int, int]] = []
    for word in blanks:
        m = re.compile(rf"(?<![A-Za-z]){re.escape(word)}(?![A-Za-z])", re.IGNORECASE).search(text, cursor)
        if m is None:
            return None
        spans.append((m.start(), m.end()))
        cursor = m.end()
    return spans


def prefix_len(word: str) -> int:
    """Real test keeps the first half of the word (rounded up) and hides the rest."""
    return (len(word) + 1) // 2


def validate_complete_words(item: CompleteWordsItem, params: CompleteWordsParams) -> list[str]:
    errors: list[str] = []
    n = word_count(item.text)
    if not in_range(n, params.words):
        errors.append(f"text has {n} words, expected {params.words}")
    if len(item.blanks) != params.blanks:
        errors.append(f"{len(item.blanks)} blanks, expected {params.blanks}")
    lowered = [b.lower() for b in item.blanks]
    if len(set(lowered)) != len(lowered):
        errors.append("blank words must be distinct")
    for b in item.blanks:
        if not b.isalpha() or len(b) < MIN_BLANK_LETTERS:
            errors.append(f"blank '{b}' must be a plain word of at least {MIN_BLANK_LETTERS} letters")
    if len(_FIRST_SENTENCE_END.findall(item.text)) < 3:
        errors.append("text needs at least 3 sentences")
    spans = locate_blanks(item.text, item.blanks)
    if spans is None:
        errors.append("a blank word is missing from the text, out of order, or only in the first sentence")
    else:
        for (_, prev_end), (start, _) in pairwise(spans):
            if not re.search(r"[A-Za-z]", item.text[prev_end:start]):
                errors.append("two blanks are adjacent words")
                break
    return errors
