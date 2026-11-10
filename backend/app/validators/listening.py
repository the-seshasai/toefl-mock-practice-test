import re

from app.difficulty import ConversationParams, ListenReplyParams, MonologueParams
from app.schemas import ConversationItem, ListenReplyItem, MonologueItem
from app.validators import in_range, word_count
from app.validators.mc import validate_questions

LISTEN_KINDS = frozenset({"gist", "main_idea", "purpose", "detail", "inference", "attitude", "next_action", "vocabulary", "organization"})
_NOT_SPOKEN = re.compile(r"[\[\]()*#_<>{}]")


def spoken_problems(text: str) -> list[str]:
    """Text goes straight to the speech engine: no stage directions, markup or digits-heavy clutter."""
    errors: list[str] = []
    if _NOT_SPOKEN.search(text):
        errors.append("spoken text contains brackets, markdown or stage directions")
    return errors


def validate_listen_reply(item: ListenReplyItem, params: ListenReplyParams) -> list[str]:
    errors = spoken_problems(item.utterance)
    n = word_count(item.utterance)
    if not in_range(n, params.words):
        errors.append(f"utterance has {n} words, expected {params.words}")
    opts = [o.strip().lower() for o in item.options]
    if len(set(opts)) != 4 or any(not o for o in opts):
        errors.append("options must be 4 distinct non-empty strings")
    if any(word_count(o) > 16 for o in item.options):
        errors.append("an option is too long for a reply")
    if any(f in o for o in opts for f in ("all of the above", "none of the above")):
        errors.append("'all/none of the above' option")
    return errors


def validate_conversation(item: ConversationItem, params: ConversationParams) -> list[str]:
    errors: list[str] = []
    for line in item.lines:
        errors += spoken_problems(line.text)
    n = sum(word_count(line.text) for line in item.lines)
    if not in_range(n, params.words):
        errors.append(f"conversation has {n} words, expected {params.words}")
    counts = [sum(1 for line in item.lines if line.speaker == s) for s in (0, 1)]
    if min(counts) < 2:
        errors.append("each speaker must speak at least twice")
    if item.lines[0].speaker != 0:
        errors.append("speaker 0 must start")
    errors += validate_questions(item.questions, params.questions, LISTEN_KINDS, " ".join(line.text for line in item.lines), min_kinds=2)
    return list(dict.fromkeys(errors))


def validate_monologue(item: MonologueItem, params: MonologueParams, min_kinds: int) -> list[str]:
    errors = spoken_problems(item.text)
    n = word_count(item.text)
    if not in_range(n, params.words):
        errors.append(f"script has {n} words, expected {params.words}")
    errors += validate_questions(item.questions, params.questions, LISTEN_KINDS, item.text, min_kinds=min_kinds)
    return errors
