"""Exam structure constants, derived from docs/FORMAT_SPEC.md. Do not scatter magic numbers elsewhere."""
import math
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

# Items per task within one section run
READING_BLANKS_PER_PARAGRAPH = 10
TASK_ITEM_COUNT: dict[TaskType, int] = {
    # Reading: counts are *sets* (a paragraph or a text/passage with its questions). Scored points:
    # 3 paragraphs x 10 blanks + ~8 daily-life questions + 2 passages x ~6 questions = ~50 (D-11).
    # Listening: counts are sets too. 16 single-item replies + 4 conversations + 3 announcements + 3 talks ~ 46-47 items (D-16).
    # Speaking: 7 Listen-and-Repeat items + 1 interview set of 4 questions = 11 scored items, 55 points (D-20).
    TaskType.LISTEN_AND_REPEAT: SPEAKING_REPEAT_ITEMS,
    TaskType.TAKE_INTERVIEW: 1,
    TaskType.LISTEN_CHOOSE_RESPONSE: 16,
    TaskType.LISTEN_CONVERSATION: 4,
    TaskType.LISTEN_ANNOUNCEMENT: 3,
    TaskType.LISTEN_ACADEMIC_TALK: 3,
    TaskType.COMPLETE_THE_WORDS: 3,
    TaskType.READ_DAILY_LIFE: 3,
    TaskType.READ_ACADEMIC: 2,
    TaskType.BUILD_A_SENTENCE: WRITING_BUILD_SENTENCE_ITEMS,
    TaskType.WRITE_EMAIL: WRITING_EMAIL_ITEMS,
    TaskType.WRITE_ACADEMIC_DISCUSSION: WRITING_DISCUSSION_ITEMS,
}

# Per-task time budgets in seconds (ETS publishes only the 23-min section total; split is our estimate, D-04)
TASK_SECONDS: dict[TaskType, int] = {
    TaskType.LISTEN_AND_REPEAT: 3 * 60,
    TaskType.TAKE_INTERVIEW: 5 * 60,
    TaskType.LISTEN_CHOOSE_RESPONSE: 6 * 60,
    TaskType.LISTEN_CONVERSATION: 7 * 60,
    TaskType.LISTEN_ANNOUNCEMENT: 5 * 60,
    TaskType.LISTEN_ACADEMIC_TALK: 11 * 60,
    TaskType.COMPLETE_THE_WORDS: 7 * 60,
    TaskType.READ_DAILY_LIFE: 8 * 60,
    TaskType.READ_ACADEMIC: 15 * 60,
    TaskType.BUILD_A_SENTENCE: 6 * 60,
    TaskType.WRITE_EMAIL: 7 * 60,
    TaskType.WRITE_ACADEMIC_DISCUSSION: 10 * 60,
}

# Scoring
BAND_MIN, BAND_MAX, BAND_STEP = 1.0, 6.0, 0.5
CONSTRUCTED_RESPONSE_MAX = 5  # Email, Discussion, each Speaking item


def round_band(x: float) -> float:
    """Clamp to [1, 6] and round to the nearest half band."""
    x = max(BAND_MIN, min(BAND_MAX, x))
    return math.floor(x / BAND_STEP + 0.5) * BAND_STEP  # half-up, not banker's rounding


def overall_band(section_bands: list[float]) -> float:
    return round_band(sum(section_bands) / len(section_bands))


# ---------- adaptive structure (Reading and Listening are two-stage adaptive) ----------

ROUTER, LOWER, UPPER, MAIN = "router", "lower", "upper", "main"
ROUTE_UP_THRESHOLD = 0.60  # router score at or above this fraction routes to the upper module (D-24)
LEVELS: tuple[Difficulty, ...] = (Difficulty.BEGINNER, Difficulty.INTERMEDIATE, Difficulty.ADVANCED)

# One entry per task: (task type, number of sets, seconds). Totals follow the ETS blueprint (D-24):
# Reading router 21 min + second module 9 min; Listening router 18 min + lower 7 min or upper 11 min.
StageTasks = tuple[tuple[TaskType, int, int], ...]
_T = TaskType
READING_ROUTER: StageTasks = ((_T.COMPLETE_THE_WORDS, 2, 300), (_T.READ_DAILY_LIFE, 2, 300), (_T.READ_ACADEMIC, 1, 660))
READING_SECOND: StageTasks = ((_T.COMPLETE_THE_WORDS, 1, 150), (_T.READ_DAILY_LIFE, 1, 120), (_T.READ_ACADEMIC, 1, 270))
LISTENING_ROUTER: StageTasks = (
    (_T.LISTEN_CHOOSE_RESPONSE, 10, 240), (_T.LISTEN_CONVERSATION, 3, 300), (_T.LISTEN_ANNOUNCEMENT, 2, 180), (_T.LISTEN_ACADEMIC_TALK, 2, 360),
)
LISTENING_LOWER: StageTasks = (
    (_T.LISTEN_CHOOSE_RESPONSE, 6, 150), (_T.LISTEN_CONVERSATION, 1, 90), (_T.LISTEN_ANNOUNCEMENT, 1, 75), (_T.LISTEN_ACADEMIC_TALK, 1, 105),
)
LISTENING_UPPER: StageTasks = (
    (_T.LISTEN_CHOOSE_RESPONSE, 6, 180), (_T.LISTEN_CONVERSATION, 1, 150), (_T.LISTEN_ANNOUNCEMENT, 1, 120), (_T.LISTEN_ACADEMIC_TALK, 1, 210),
)
ADAPTIVE_STAGES: dict[Section, dict[str, StageTasks]] = {
    Section.READING: {ROUTER: READING_ROUTER, LOWER: READING_SECOND, UPPER: READING_SECOND},
    Section.LISTENING: {ROUTER: LISTENING_ROUTER, LOWER: LISTENING_LOWER, UPPER: LISTENING_UPPER},
}


def shift_level(level: Difficulty, delta: int) -> Difficulty:
    """One step up or down the Beginner < Intermediate < Advanced ladder, clamped at the ends."""
    return LEVELS[max(0, min(len(LEVELS) - 1, LEVELS.index(level) + delta))]


def route_levels(router_level: Difficulty) -> dict[str, Difficulty]:
    return {LOWER: shift_level(router_level, -1), UPPER: shift_level(router_level, +1)}
