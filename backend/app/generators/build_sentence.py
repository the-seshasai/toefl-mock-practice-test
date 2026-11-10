from typing import Any

from app.difficulty import BUILD_SENTENCE, BuildSentenceParams
from app.generators.base import TaskGenerator, shuffled_different
from app.schemas import BuildSentenceItem
from app.spec import Difficulty, TaskType
from app.validators.build_sentence import validate_build_sentence


class BuildSentenceGenerator(TaskGenerator):
    task_type = TaskType.BUILD_A_SENTENCE
    prompt_file = "build_sentence.md"
    item_model = BuildSentenceItem
    max_batch = 12

    def params(self, difficulty: Difficulty) -> BuildSentenceParams:
        return BUILD_SENTENCE[difficulty]

    def validate(self, item: BuildSentenceItem, params: BuildSentenceParams) -> list[str]:
        return validate_build_sentence(item, params)

    def content_key(self, item: BuildSentenceItem) -> str:
        return " ".join(item.correct_order)

    def to_payload(self, item: BuildSentenceItem, difficulty: Difficulty = Difficulty.INTERMEDIATE) -> dict[str, Any]:
        data = item.model_dump()
        data["chunks"] = shuffled_different(item.correct_order, [item.correct_order, *item.acceptable_orders])
        return data

    def public_prompt(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"context": payload["context"], "chunks": payload["chunks"]}

    def clean_answer(self, answer: dict[str, Any]) -> dict[str, Any]:
        order = answer.get("order", [])
        if not isinstance(order, list) or len(order) > 30 or not all(isinstance(c, str) and len(c) < 200 for c in order):
            raise ValueError("order must be a list of chunk strings")
        return {"order": order}

    def prompt_vars(self, params: BuildSentenceParams, count: int, avoid: list[str]) -> dict[str, str]:
        structures = [params.structures[i % len(params.structures)] for i in range(count)]
        return {
            "word_min": str(params.words[0]), "word_max": str(params.words[1]),
            "chunk_min": str(params.chunks[0]), "chunk_max": str(params.chunks[1]),
            "grammar": params.grammar, "vocabulary": params.vocabulary,
            "patterns": "; ".join(f"{i + 1}) {s}" for i, s in enumerate(structures)),
        }
