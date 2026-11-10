from typing import Any

from app.difficulty import DISCUSSION, DiscussionParams
from app.generators.base import TaskGenerator, aim, clean_text_answer
from app.schemas import DiscussionItem
from app.spec import Difficulty, TaskType
from app.validators.write_discussion import validate_discussion


class WriteDiscussionGenerator(TaskGenerator):
    task_type = TaskType.WRITE_ACADEMIC_DISCUSSION
    prompt_file = "write_academic_discussion.md"
    item_model = DiscussionItem

    def params(self, difficulty: Difficulty) -> DiscussionParams:
        return DISCUSSION[difficulty]

    def validate(self, item: DiscussionItem, params: DiscussionParams) -> list[str]:
        return validate_discussion(item, params)

    def content_key(self, item: DiscussionItem) -> str:
        return item.professor_post

    def to_payload(self, item: DiscussionItem, difficulty: Difficulty = Difficulty.INTERMEDIATE) -> dict[str, Any]:
        return item.model_dump()

    def clean_answer(self, answer: dict[str, Any]) -> dict[str, Any]:
        return clean_text_answer(answer)

    def prompt_vars(self, params: DiscussionParams, count: int, avoid: list[str]) -> dict[str, str]:
        return {
            "prof_min": aim(params.professor_words)[0], "prof_max": aim(params.professor_words)[1],
            "student_min": aim(params.student_words)[0], "student_max": aim(params.student_words)[1],
            "vocabulary": params.vocabulary, "stance": params.stance,
        }
