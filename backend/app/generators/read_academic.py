from typing import Any

from app.difficulty import ACADEMIC, AcademicParams
from app.generators.base import TaskGenerator, aim
from app.generators.mc import clean_choices, public_questions, shuffled_questions
from app.schemas import AcademicPassageItem
from app.spec import Difficulty, TaskType
from app.validators.read_academic import validate_academic


class ReadAcademicGenerator(TaskGenerator):
    task_type = TaskType.READ_ACADEMIC
    prompt_file = "read_academic_passage.md"
    item_model = AcademicPassageItem
    max_batch = 3

    def params(self, difficulty: Difficulty) -> AcademicParams:
        return ACADEMIC[difficulty]

    def validate(self, item: AcademicPassageItem, params: AcademicParams) -> list[str]:
        return validate_academic(item, params)

    def content_key(self, item: AcademicPassageItem) -> str:
        return item.passage

    def to_payload(self, item: AcademicPassageItem, difficulty: Difficulty = Difficulty.INTERMEDIATE) -> dict[str, Any]:
        return {"topic": item.topic, "title": item.title, "passage": item.passage,
                "questions": shuffled_questions(item.questions)}

    def public_prompt(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"title": payload["title"], "passage": payload["passage"],
                "questions": public_questions(payload["questions"])}

    def clean_answer(self, answer: dict[str, Any]) -> dict[str, Any]:
        return clean_choices(answer)

    def prompt_vars(self, params: AcademicParams, count: int, avoid: list[str]) -> dict[str, str]:
        return {
            "word_min": aim(params.words)[0], "word_max": aim(params.words)[1],
            "q_min": str(params.questions[0]), "q_max": str(params.questions[1]),
            "vocabulary": params.vocabulary, "inference": params.inference_depth, "distractors": params.distractors,
            "sentence_words": str(params.sentence_words), "fk_target": f"{(max(params.fk[0], 4.0) + params.fk[1]) / 2:.1f}",
            "fk_min": f"{params.fk[0]:.1f}", "fk_max": f"{params.fk[1]:.1f}",
        }
