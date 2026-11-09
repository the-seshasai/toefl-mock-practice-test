"""Exam structure constants, derived from docs/FORMAT_SPEC.md. Do not scatter magic numbers elsewhere."""
from enum import StrEnum


class Section(StrEnum):
    READING = "reading"
    LISTENING = "listening"
    WRITING = "writing"
    SPEAKING = "speaking"


class Difficulty(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class TaskType(StrEnum):
    COMPLETE_THE_WORDS = "complete_the_words"
    READ_DAILY_LIFE = "read_in_daily_life"
    READ_ACADEMIC = "read_academic_passage"
    LISTEN_CHOOSE_RESPONSE = "listen_choose_response"
    LISTEN_CONVERSATION = "listen_conversation"
    LISTEN_ANNOUNCEMENT = "listen_announcement"
    LISTEN_ACADEMIC_TALK = "listen_academic_talk"
    BUILD_A_SENTENCE = "build_a_sentence"
    WRITE_EMAIL = "write_email"
    WRITE_ACADEMIC_DISCUSSION = "write_academic_discussion"
    LISTEN_AND_REPEAT = "listen_and_repeat"
    TAKE_INTERVIEW = "take_interview"


SECTION_ORDER: tuple[Section, ...] = (
    Section.READING, Section.LISTENING, Section.WRITING, Section.SPEAKING,
)

SECTION_TASKS: dict[Section, tuple[TaskType, ...]] = {
    Section.READING: (TaskType.COMPLETE_THE_WORDS, TaskType.READ_DAILY_LIFE, TaskType.READ_ACADEMIC),
    Section.LISTENING: (
        TaskType.LISTEN_CHOOSE_RESPONSE, TaskType.LISTEN_CONVERSATION,
        TaskType.LISTEN_ANNOUNCEMENT, TaskType.LISTEN_ACADEMIC_TALK,
    ),
    Section.WRITING: (TaskType.BUILD_A_SENTENCE, TaskType.WRITE_EMAIL, TaskType.WRITE_ACADEMIC_DISCUSSION),
    Section.SPEAKING: (TaskType.LISTEN_AND_REPEAT, TaskType.TAKE_INTERVIEW),
}

TASK_SECTION: dict[TaskType, Section] = {t: s for s, ts in SECTION_TASKS.items() for t in ts}

# Official totals (items, approx. base minutes)
SECTION_ITEMS: dict[Section, int] = {
    Section.READING: 50, Section.LISTENING: 47, Section.WRITING: 12, Section.SPEAKING: 11,
}
SECTION_MINUTES: dict[Section, int] = {
    Section.READING: 30, Section.LISTENING: 29, Section.WRITING: 23, Section.SPEAKING: 8,
}
ADAPTIVE_SECTIONS: frozenset[Section] = frozenset({Section.READING, Section.LISTENING})

# Writing / Speaking item counts per task
WRITING_BUILD_SENTENCE_ITEMS = 10
WRITING_EMAIL_ITEMS = 1
WRITING_DISCUSSION_ITEMS = 1
SPEAKING_REPEAT_ITEMS = 7
SPEAKING_INTERVIEW_ITEMS = 4

# Scoring
BAND_MIN, BAND_MAX, BAND_STEP = 1.0, 6.0, 0.5
CONSTRUCTED_RESPONSE_MAX = 5  # Email, Discussion, each Speaking item


def round_band(x: float) -> float:
    """Clamp to [1, 6] and round to the nearest half band."""
    x = max(BAND_MIN, min(BAND_MAX, x))
    return round(x / BAND_STEP) * BAND_STEP


def overall_band(section_bands: list[float]) -> float:
    return round_band(sum(section_bands) / len(section_bands))
