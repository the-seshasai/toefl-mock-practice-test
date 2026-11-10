from app.difficulty import AcademicParams
from app.schemas import AcademicPassageItem
from app.validators import in_range, word_count
from app.validators.mc import validate_questions
from app.validators.readability import fk_grade

ACADEMIC_KINDS = frozenset({"main_idea", "detail", "negative_detail", "inference", "vocabulary", "rhetorical_purpose", "reference"})


def validate_academic(item: AcademicPassageItem, params: AcademicParams) -> list[str]:
    errors: list[str] = []
    n = word_count(item.passage)
    if not in_range(n, params.words):
        errors.append(f"passage has {n} words, expected {params.words}")
    grade = fk_grade(item.passage)
    if not params.fk[0] <= grade <= params.fk[1]:
        errors.append(f"readability grade {grade:.1f} outside {params.fk} for this level")
    if item.passage.count("\n\n") < 1:
        errors.append("passage needs at least two paragraphs")
    errors += validate_questions(item.questions, params.questions, ACADEMIC_KINDS, item.passage, min_kinds=3)
    return errors
