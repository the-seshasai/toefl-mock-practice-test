from app.difficulty import InterviewParams, RepeatParams
from app.schemas import InterviewItem, RepeatItem
from app.validators import in_range, word_count
from app.validators.listening import spoken_problems


def validate_repeat(item: RepeatItem, params: RepeatParams) -> list[str]:
    errors = spoken_problems(item.sentence)
    n = word_count(item.sentence)
    if not in_range(n, params.words):
        errors.append(f"sentence has {n} words, expected {params.words}")
    if item.sentence.strip()[-1:] not in ".?!":
        errors.append("sentence must end with . ? or !")
    if sum(ch.isdigit() for ch in item.sentence) > 0:
        errors.append("write numbers as words so they are spoken and transcribed consistently")
    return errors


def validate_interview(item: InterviewItem, params: InterviewParams) -> list[str]:
    errors: list[str] = []
    for q in item.questions:
        errors += spoken_problems(q)
        n = word_count(q)
        if not in_range(n, params.question_words):
            errors.append(f"question has {n} words, expected {params.question_words}")
    if len({q.strip().lower() for q in item.questions}) != 4:
        errors.append("questions must be distinct")
    if sum("?" in q for q in item.questions) < 3:
        errors.append("at least three questions must be actual questions")
    return list(dict.fromkeys(errors))
