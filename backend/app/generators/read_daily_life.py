import random
from typing import Any

from app.difficulty import DAILY_LIFE, DailyLifeParams
from app.generators.base import TaskGenerator, aim
from app.generators.mc import clean_choices, public_questions, shuffled_questions
from app.schemas import DailyLifeItem
from app.spec import Difficulty, TaskType
from app.validators.read_daily_life import validate_daily_life


class ReadDailyLifeGenerator(TaskGenerator):
    task_type = TaskType.READ_DAILY_LIFE
    prompt_file = "read_daily_life.md"
    item_model = DailyLifeItem
    max_batch = 4

    def params(self, difficulty: Difficulty) -> DailyLifeParams:
        return DAILY_LIFE[difficulty]

    def validate(self, item: DailyLifeItem, params: DailyLifeParams) -> list[str]:
        return validate_daily_life(item, params)

    def content_key(self, item: DailyLifeItem) -> str:
        return item.text

    def to_payload(self, item: DailyLifeItem, difficulty: Difficulty = Difficulty.INTERMEDIATE) -> dict[str, Any]:
        return {"topic": item.topic, "format": item.format, "title": item.title, "text": item.text,
                "questions": shuffled_questions(item.questions)}

    def public_prompt(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"format": payload["format"], "title": payload["title"], "text": payload["text"],
                "questions": public_questions(payload["questions"])}

    def clean_answer(self, answer: dict[str, Any]) -> dict[str, Any]:
        return clean_choices(answer)

    def prompt_vars(self, params: DailyLifeParams, count: int, avoid: list[str]) -> dict[str, str]:
        formats = random.sample(params.formats, min(count, len(params.formats)))
        return {
            "word_min": aim(params.words)[0], "word_max": aim(params.words)[1],
            "q_min": str(params.questions[0]), "q_max": str(params.questions[1]),
            "vocabulary": params.vocabulary, "inference": params.inference_depth, "distractors": params.distractors,
            "formats": "; ".join(f"{i + 1}) {f}" for i, f in enumerate(formats)),
        }
