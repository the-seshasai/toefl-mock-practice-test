from typing import Any

from app.audio.stt import Transcriber
from app.config import settings
from app.llm import LLMProvider
from app.scoring.reading import score_complete_words, score_mc_set
from app.scoring.speaking import score_interview, score_repeat
from app.scoring.writing import score_build_sentence, score_text_task
from app.spec import Difficulty, TaskType


def score_response(llm: LLMProvider, task_type: TaskType, payload: dict[str, Any], answer: dict[str, Any] | None,
                   difficulty: Difficulty, stt: Transcriber | None = None) -> tuple[float, float, dict[str, Any]]:
    """Return (points, max_points, feedback). LLM-scored tasks can raise LLMError; speaking can raise SttError."""
    match task_type:
        case TaskType.BUILD_A_SENTENCE:
            return score_build_sentence(payload, answer)
        case TaskType.COMPLETE_THE_WORDS:
            return score_complete_words(payload, answer)
        case (
            TaskType.READ_DAILY_LIFE | TaskType.READ_ACADEMIC | TaskType.LISTEN_CHOOSE_RESPONSE | TaskType.LISTEN_CONVERSATION
            | TaskType.LISTEN_ANNOUNCEMENT | TaskType.LISTEN_ACADEMIC_TALK
        ):
            return score_mc_set(payload, answer)
        case TaskType.WRITE_EMAIL | TaskType.WRITE_ACADEMIC_DISCUSSION:
            return score_text_task(llm, task_type, payload, answer, difficulty)
        case TaskType.LISTEN_AND_REPEAT:
            assert stt is not None
            return score_repeat(payload, answer, stt, settings.recordings_dir)
        case TaskType.TAKE_INTERVIEW:
            assert stt is not None
            return score_interview(llm, stt, payload, answer, difficulty, settings.recordings_dir)
    raise ValueError(f"No scorer for {task_type.value}")
