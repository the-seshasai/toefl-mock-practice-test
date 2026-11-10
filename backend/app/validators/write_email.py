from app.difficulty import EmailParams
from app.schemas import EmailItem
from app.validators import in_range, word_count


def validate_email(item: EmailItem, params: EmailParams) -> list[str]:
    errors: list[str] = []
    n = word_count(item.scenario)
    if not in_range(n, params.scenario_words):
        errors.append(f"scenario has {n} words, expected {params.scenario_words}")
    if not in_range(len(item.points), params.points):
        errors.append(f"{len(item.points)} points, expected {params.points}")
    if any(not p.strip() for p in item.points):
        errors.append("a point is empty")
    return errors
