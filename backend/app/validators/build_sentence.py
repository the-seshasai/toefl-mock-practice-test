from collections import Counter

from app.difficulty import BuildSentenceParams
from app.schemas import BuildSentenceItem
from app.validators import in_range, word_count


def validate_build_sentence(item: BuildSentenceItem, params: BuildSentenceParams) -> list[str]:
    """Return a list of problems; empty means the item is acceptable."""
    errors: list[str] = []
    chunks = item.correct_order
    if any(not c.strip() for c in chunks):
        errors.append("empty chunk")
    if not in_range(len(chunks), params.chunks):
        errors.append(f"chunk count {len(chunks)} outside {params.chunks}")
    words = sum(word_count(c) for c in chunks)
    if not in_range(words, params.words):
        errors.append(f"word count {words} outside {params.words}")
    if any(word_count(c) > 4 for c in chunks):
        errors.append("a chunk has more than 4 words")
    normalized = [c.strip().lower() for c in chunks]
    if len(set(normalized)) != len(normalized):
        errors.append("duplicate chunks make the ordering ambiguous")
    if not chunks or chunks[-1].strip()[-1:] not in ".?!":
        errors.append("sentence must end with . ? or !")
    if any(c.strip()[-1:] in ".?!" for c in chunks[:-1]):
        errors.append("terminal punctuation inside a non-final chunk")
    base = Counter(normalized)
    seen = {tuple(normalized)}
    for alt in item.acceptable_orders:
        alt_n = tuple(c.strip().lower() for c in alt)
        if Counter(alt_n) != base:
            errors.append("acceptable_orders must be permutations of the same chunks")
        elif alt_n in seen:
            errors.append("acceptable order duplicates another order")
        seen.add(alt_n)
    if len(item.acceptable_orders) > 3:
        errors.append("too many alternative orders: the item is not unambiguous enough")
    return errors
