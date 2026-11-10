from typing import Any

from app.difficulty import COMPLETE_WORDS, CompleteWordsParams
from app.generators.base import TaskGenerator, aim
from app.schemas import CompleteWordsItem
from app.spec import Difficulty, TaskType
from app.validators.complete_words import (
    locate_blanks,
    prefix_len,
    validate_complete_words,
)

MAX_LETTERS = 20


class CompleteWordsGenerator(TaskGenerator):
    task_type = TaskType.COMPLETE_THE_WORDS
    prompt_file = "complete_the_words.md"
    item_model = CompleteWordsItem
    max_batch = 4

    def params(self, difficulty: Difficulty) -> CompleteWordsParams:
        return COMPLETE_WORDS[difficulty]

    def validate(self, item: CompleteWordsItem, params: CompleteWordsParams) -> list[str]:
        return validate_complete_words(item, params)

    def content_key(self, item: CompleteWordsItem) -> str:
        return item.text

    def to_payload(self, item: CompleteWordsItem, difficulty: Difficulty = Difficulty.INTERMEDIATE) -> dict[str, Any]:
        spans = locate_blanks(item.text, item.blanks)
        assert spans is not None  # guaranteed by validate()
        blanks: list[dict[str, Any]] = []
        segments: list[dict[str, Any]] = []
        cursor = 0
        for i, (start, end) in enumerate(spans):
            word = item.text[start:end]
            keep = prefix_len(word)
            if start > cursor:
                segments.append({"text": item.text[cursor:start]})
            segments.append({"blank": i, "prefix": word[:keep], "missing": len(word) - keep})
            blanks.append({"answer": word, "prefix": word[:keep], "missing": len(word) - keep})
            cursor = end
        if cursor < len(item.text):
            segments.append({"text": item.text[cursor:]})
        return {"topic": item.topic, "text": item.text, "blanks": blanks, "segments": segments}

    def public_prompt(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"segments": payload["segments"]}

    def clean_answer(self, answer: dict[str, Any]) -> dict[str, Any]:
        letters = answer.get("letters", [])
        if not isinstance(letters, list) or len(letters) > 30 or not all(isinstance(s, str) and len(s) <= MAX_LETTERS for s in letters):
            raise ValueError("letters must be a list of short strings")
        return {"letters": letters}

    def prompt_vars(self, params: CompleteWordsParams, count: int, avoid: list[str]) -> dict[str, str]:
        return {
            "word_min": aim(params.words)[0], "word_max": aim(params.words)[1],
            "vocabulary": params.vocabulary, "blank_count": str(params.blanks),
        }
