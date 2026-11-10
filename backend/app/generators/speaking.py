import random
from typing import Any

from app.difficulty import INTERVIEW, REPEAT, InterviewParams, RepeatParams
from app.generators.base import TaskGenerator, aim
from app.schemas import InterviewItem, RepeatItem
from app.spec import Difficulty, TaskType
from app.validators.speaking import validate_interview, validate_repeat

MIN_RESPONSE_SECONDS, MAX_RESPONSE_SECONDS = 8, 30


class RepeatGenerator(TaskGenerator):
    task_type = TaskType.LISTEN_AND_REPEAT
    prompt_file = "listen_and_repeat.md"
    item_model = RepeatItem
    max_batch = 9

    def params(self, difficulty: Difficulty) -> RepeatParams:
        return REPEAT[difficulty]

    def validate(self, item: RepeatItem, params: RepeatParams) -> list[str]:
        return validate_repeat(item, params)

    def content_key(self, item: RepeatItem) -> str:
        return item.sentence

    def to_payload(self, item: RepeatItem, difficulty: Difficulty = Difficulty.INTERMEDIATE) -> dict[str, Any]:
        params = REPEAT[difficulty]
        words = len(item.sentence.split())
        seconds = round(min(MAX_RESPONSE_SECONDS, max(MIN_RESPONSE_SECONDS, params.base_seconds + params.per_word_seconds * words)))
        return {
            "topic": item.topic, "sentence": item.sentence, "word_count": words, "response_seconds": seconds,
            "setting": "Listen to the sentence, then repeat it exactly.", "length_scale": params.length_scale,
            "script": [{"speaker": "Speaker", "gender": random.choice(["male", "female"]), "text": item.sentence}],
        }

    def order_key(self, payload: dict[str, Any]) -> float:
        return payload["word_count"]  # sentences get longer through the task, as on the real test

    def public_prompt(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"setting": payload["setting"], "has_audio": True, "response_seconds": payload["response_seconds"], "parts": 1,
                "prep_seconds": 0}

    def clean_answer(self, answer: dict[str, Any]) -> dict[str, Any]:
        raise ValueError("Speaking answers are recordings; upload them instead")

    def prompt_vars(self, params: RepeatParams, count: int, avoid: list[str]) -> dict[str, str]:
        lo, hi = params.words
        lengths = [round(lo + (hi - lo) * i / max(count - 1, 1)) for i in range(count)]
        return {"vocabulary": params.vocabulary, "structures": params.structures, "word_min": str(lo), "word_max": str(hi),
                "lengths": "; ".join(f"{i + 1}) about {n} words" for i, n in enumerate(lengths))}


class InterviewGenerator(TaskGenerator):
    task_type = TaskType.TAKE_INTERVIEW
    prompt_file = "take_interview.md"
    item_model = InterviewItem
    max_batch = 2

    def params(self, difficulty: Difficulty) -> InterviewParams:
        return INTERVIEW[difficulty]

    def validate(self, item: InterviewItem, params: InterviewParams) -> list[str]:
        return validate_interview(item, params)

    def content_key(self, item: InterviewItem) -> str:
        return " ".join(item.questions)

    def to_payload(self, item: InterviewItem, difficulty: Difficulty = Difficulty.INTERMEDIATE) -> dict[str, Any]:
        params = INTERVIEW[difficulty]
        name = item.interviewer.name or "Interviewer"
        return {
            "topic": item.topic, "setting": item.setting, "questions": item.questions,
            "prep_seconds": params.prep_seconds, "response_seconds": params.response_seconds,
            "audio_parts": [{"script": [{"speaker": name, "gender": item.interviewer.gender, "text": q}],
                             "length_scale": params.length_scale} for q in item.questions],
        }

    def public_prompt(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"setting": payload["setting"], "has_audio": True, "parts": len(payload["questions"]),
                "prep_seconds": payload["prep_seconds"], "response_seconds": payload["response_seconds"]}

    def clean_answer(self, answer: dict[str, Any]) -> dict[str, Any]:
        raise ValueError("Speaking answers are recordings; upload them instead")

    def prompt_vars(self, params: InterviewParams, count: int, avoid: list[str]) -> dict[str, str]:
        return {"word_min": aim(params.question_words)[0], "word_max": aim(params.question_words)[1],
                "vocabulary": params.vocabulary, "depth": params.depth}
