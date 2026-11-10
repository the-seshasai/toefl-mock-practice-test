from app.difficulty import DiscussionParams
from app.schemas import DiscussionItem
from app.validators import in_range, word_count


def validate_discussion(item: DiscussionItem, params: DiscussionParams) -> list[str]:
    errors: list[str] = []
    n = word_count(item.professor_post)
    if not in_range(n, params.professor_words):
        errors.append(f"professor post has {n} words, expected {params.professor_words}")
    if "?" not in item.professor_post:
        errors.append("professor post must pose a question")
    if len(item.students) != 2:
        errors.append("exactly two student posts required")
    for s in item.students:
        m = word_count(s.text)
        if not in_range(m, params.student_words):
            errors.append(f"student post by {s.name} has {m} words, expected {params.student_words}")
    names = {s.name.strip().lower() for s in item.students}
    if len(names) != len(item.students):
        errors.append("student names must differ")
    if item.students and item.students[0].text.strip().lower() == item.students[-1].text.strip().lower():
        errors.append("student posts are identical")
    return errors
