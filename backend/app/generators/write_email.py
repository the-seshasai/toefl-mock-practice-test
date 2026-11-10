from typing import Any

from app.difficulty import EMAIL, EmailParams
from app.generators.base import TaskGenerator, aim, clean_text_answer
from app.schemas import EmailItem
from app.spec import Difficulty, TaskType
from app.validators.write_email import validate_email


class WriteEmailGenerator(TaskGenerator):
    task_type = TaskType.WRITE_EMAIL
    prompt_file = "write_email.md"
    item_model = EmailItem

    def params(self, difficulty: Difficulty) -> EmailParams:
        return EMAIL[difficulty]

    def validate(self, item: EmailItem, params: EmailParams) -> list[str]:
        return validate_email(item, params)

    def content_key(self, item: EmailItem) -> str:
        return item.scenario

    def to_payload(self, item: EmailItem, difficulty: Difficulty = Difficulty.INTERMEDIATE) -> dict[str, Any]:
        return item.model_dump()

    def clean_answer(self, answer: dict[str, Any]) -> dict[str, Any]:
        return clean_text_answer(answer)

    def prompt_vars(self, params: EmailParams, count: int, avoid: list[str]) -> dict[str, str]:
        return {
            "scenario_min": aim(params.scenario_words)[0], "scenario_max": aim(params.scenario_words)[1],
            "points_min": str(params.points[0]), "points_max": str(params.points[1]),
            "register": params.register, "vocabulary": params.vocabulary,
        }
