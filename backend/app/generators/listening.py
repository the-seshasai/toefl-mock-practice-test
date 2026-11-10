"""Listening generators. Voices are assigned in code (not by the LLM) and audio is built after generation."""
import random
from typing import Any

from app.difficulty import (
    ACADEMIC_TALK,
    ANNOUNCEMENT,
    CONVERSATION,
    LISTEN_REPLY,
    ConversationParams,
    ListenReplyParams,
    MonologueParams,
)
from app.generators.base import TaskGenerator, aim
from app.generators.mc import clean_choices, public_questions, shuffled_questions
from app.schemas import ConversationItem, ListenReplyItem, MCQuestion, MonologueItem
from app.spec import Difficulty, TaskType
from app.validators.listening import (
    validate_conversation,
    validate_listen_reply,
    validate_monologue,
)


def _payload(topic: str, setting: str, script: list[dict[str, Any]], questions: list[dict[str, Any]], scale: float) -> dict[str, Any]:
    """Voices and the audio key are added later, when the audio is built (see services.exam._build_audio)."""
    return {"topic": topic, "setting": setting, "script": script, "questions": questions, "length_scale": scale}


class ListeningGenerator(TaskGenerator):
    """Shared public view / answer handling for all four listening tasks."""

    def payload_key(self, payload: dict[str, Any]) -> str:
        return " ".join(line["text"] for line in payload["script"])

    def public_prompt(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"setting": payload["setting"], "has_audio": True, "questions": public_questions(payload["questions"])}

    def clean_answer(self, answer: dict[str, Any]) -> dict[str, Any]:
        return clean_choices(answer)


class ListenReplyGenerator(ListeningGenerator):
    task_type = TaskType.LISTEN_CHOOSE_RESPONSE
    prompt_file = "listen_choose_response.md"
    item_model = ListenReplyItem
    max_batch = 18

    def params(self, difficulty: Difficulty) -> ListenReplyParams:
        return LISTEN_REPLY[difficulty]

    def validate(self, item: ListenReplyItem, params: ListenReplyParams) -> list[str]:
        return validate_listen_reply(item, params)

    def content_key(self, item: ListenReplyItem) -> str:
        return item.utterance

    def to_payload(self, item: ListenReplyItem, difficulty: Difficulty = Difficulty.INTERMEDIATE) -> dict[str, Any]:
        scale = LISTEN_REPLY[difficulty].length_scale
        gender = random.choice(["male", "female"])
        q = MCQuestion(prompt="Choose the best response.", options=item.options, answer=item.answer, kind="response",
                       explanation=item.explanation)
        return _payload(item.topic, "Listen to the speaker, then choose the best reply.",
                        [{"speaker": "Speaker", "gender": gender, "text": item.utterance}], shuffled_questions([q]), scale)

    def prompt_vars(self, params: ListenReplyParams, count: int, avoid: list[str]) -> dict[str, str]:
        return {"word_min": aim(params.words)[0], "word_max": aim(params.words)[1], "vocabulary": params.vocabulary,
                "distractors": params.distractors}


class ConversationGenerator(ListeningGenerator):
    task_type = TaskType.LISTEN_CONVERSATION
    prompt_file = "listen_conversation.md"
    item_model = ConversationItem
    max_batch = 4

    def params(self, difficulty: Difficulty) -> ConversationParams:
        return CONVERSATION[difficulty]

    def validate(self, item: ConversationItem, params: ConversationParams) -> list[str]:
        return validate_conversation(item, params)

    def content_key(self, item: ConversationItem) -> str:
        return " ".join(line.text for line in item.lines)

    def to_payload(self, item: ConversationItem, difficulty: Difficulty = Difficulty.INTERMEDIATE) -> dict[str, Any]:
        names = [s.name or f"Speaker {i + 1}" for i, s in enumerate(item.speakers)]
        if names[0] == names[1]:
            names[1] += " (2)"
        script = [{"speaker": names[line.speaker], "gender": item.speakers[line.speaker].gender, "text": line.text}
                  for line in item.lines]
        return _payload(item.topic, item.setting, script, shuffled_questions(item.questions), CONVERSATION[difficulty].length_scale)

    def prompt_vars(self, params: ConversationParams, count: int, avoid: list[str]) -> dict[str, str]:
        return {"word_min": aim(params.words)[0], "word_max": aim(params.words)[1], "q_min": str(params.questions[0]),
                "q_max": str(params.questions[1]), "vocabulary": params.vocabulary, "inference": params.inference_depth,
                "distractors": params.distractors}


class MonologueGenerator(ListeningGenerator):
    item_model = MonologueItem
    min_kinds = 2
    table: dict[Difficulty, MonologueParams]

    def params(self, difficulty: Difficulty) -> MonologueParams:
        return self.table[difficulty]

    def validate(self, item: MonologueItem, params: MonologueParams) -> list[str]:
        return validate_monologue(item, params, self.min_kinds)

    def content_key(self, item: MonologueItem) -> str:
        return item.text

    def to_payload(self, item: MonologueItem, difficulty: Difficulty = Difficulty.INTERMEDIATE) -> dict[str, Any]:
        script = [{"speaker": item.speaker.name or "Speaker", "gender": item.speaker.gender, "text": item.text}]
        return _payload(item.topic, item.setting, script, shuffled_questions(item.questions), self.table[difficulty].length_scale)

    def prompt_vars(self, params: MonologueParams, count: int, avoid: list[str]) -> dict[str, str]:
        return {"word_min": aim(params.words)[0], "word_max": aim(params.words)[1], "q_min": str(params.questions[0]),
                "q_max": str(params.questions[1]), "vocabulary": params.vocabulary, "inference": params.inference_depth,
                "distractors": params.distractors}


class AnnouncementGenerator(MonologueGenerator):
    task_type = TaskType.LISTEN_ANNOUNCEMENT
    prompt_file = "listen_announcement.md"
    table = ANNOUNCEMENT
    max_batch = 4


class AcademicTalkGenerator(MonologueGenerator):
    task_type = TaskType.LISTEN_ACADEMIC_TALK
    prompt_file = "listen_academic_talk.md"
    table = ACADEMIC_TALK
    min_kinds = 3
    max_batch = 3
