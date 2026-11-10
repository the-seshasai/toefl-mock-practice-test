import re

from app.schemas import MCQuestion
from app.validators import in_range

FORBIDDEN_OPTIONS = ("all of the above", "none of the above", "both a and b", "a and b")
# A quoted word or short phrase. The opening quote must not follow a letter, so possessives ("professor's") are not quotes.
_QUOTED = re.compile(r"(?<![A-Za-z])[\"'‘“]([A-Za-z][A-Za-z -]{1,40}?)[\"'’”]")


def _all_words_in(phrase: str, lowered_source: str) -> bool:
    return all(re.search(rf"(?<![a-z]){re.escape(w)}", lowered_source) for w in phrase.lower().split())


def normalize_kind(kind: str) -> str:
    return re.sub(r"[^a-z]+", "_", kind.lower()).strip("_")


def validate_questions(questions: list[MCQuestion], count: tuple[int, int], kinds: frozenset[str],
                       source_text: str, min_kinds: int) -> list[str]:
    """Shared multiple-choice checks: exactly one keyed answer, 4 distinct options, sane kinds, vocab words present."""
    errors: list[str] = []
    if not in_range(len(questions), count):
        errors.append(f"{len(questions)} questions, expected {count}")
    seen_prompts: set[str] = set()
    used_kinds: set[str] = set()
    lowered_source = source_text.lower()
    for i, q in enumerate(questions, 1):
        opts = [o.strip().lower() for o in q.options]
        if len(set(opts)) != 4 or any(not o for o in opts):
            errors.append(f"q{i}: options must be 4 distinct non-empty strings")
        if any(f in o for o in opts for f in FORBIDDEN_OPTIONS):
            errors.append(f"q{i}: 'all/none of the above' style option")
        kind = normalize_kind(q.kind)
        used_kinds.add(kind)
        if kind not in kinds:
            errors.append(f"q{i}: unknown kind '{q.kind}'")
        if q.prompt.strip().lower() in seen_prompts:
            errors.append(f"q{i}: duplicate question")
        seen_prompts.add(q.prompt.strip().lower())
        if kind == "vocabulary":
            quoted = _QUOTED.findall(q.prompt)
            if not quoted or not any(_all_words_in(phrase, lowered_source) for phrase in quoted):
                errors.append(f"q{i}: vocabulary question must quote a word from the text")
    if len(used_kinds & kinds) < min_kinds:
        errors.append(f"needs at least {min_kinds} different question kinds")
    return errors
