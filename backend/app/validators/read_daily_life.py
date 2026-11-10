from app.difficulty import DailyLifeParams
from app.schemas import DailyLifeItem
from app.validators import in_range, word_count
from app.validators.mc import validate_questions

DAILY_LIFE_KINDS = frozenset({"main_purpose", "detail", "inference", "vocabulary", "reference"})


def validate_daily_life(item: DailyLifeItem, params: DailyLifeParams) -> list[str]:
    errors: list[str] = []
    n = word_count(item.text)
    if not in_range(n, params.words):
        errors.append(f"text has {n} words, expected {params.words}")
    errors += validate_questions(item.questions, params.questions, DAILY_LIFE_KINDS, item.text, min_kinds=2)
    return errors
