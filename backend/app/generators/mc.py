"""Shared multiple-choice helpers for Reading (and later Listening) item sets."""
import random
from typing import Any

from app.schemas import MCQuestion
from app.validators.mc import normalize_kind

MAX_CHOICES_LEN = 40


def shuffled_questions(questions: list[MCQuestion]) -> list[dict[str, Any]]:
    """Shuffle each question's options (LLMs bias toward A/B) and re-key the answer index."""
    out: list[dict[str, Any]] = []
    for q in questions:
        order = list(range(4))
        random.shuffle(order)
        out.append({
            "prompt": q.prompt, "options": [q.options[i] for i in order], "answer": order.index(q.answer),
            "kind": normalize_kind(q.kind), "explanation": q.explanation,
        })
    return out


def public_questions(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"prompt": q["prompt"], "options": q["options"]} for q in questions]


def clean_choices(answer: dict[str, Any]) -> dict[str, Any]:
    choices = answer.get("choices", [])
    if not isinstance(choices, list) or len(choices) > MAX_CHOICES_LEN or not all(
        c is None or (isinstance(c, int) and not isinstance(c, bool) and 0 <= c <= 3) for c in choices
    ):
        raise ValueError("choices must be a list of option indexes 0-3 or null")
    return {"choices": choices}
