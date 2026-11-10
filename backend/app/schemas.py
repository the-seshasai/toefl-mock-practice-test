"""Item payload models (what generators produce/store) and API models."""
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.spec import Difficulty, Section, TaskType

# ---------- item payloads ----------


class RawBatch(BaseModel):
    """LLM batch envelope; items are validated one by one so one bad item doesn't sink the batch."""

    items: list[dict[str, Any]]


class BuildSentenceItem(BaseModel):
    context: str = Field(min_length=8)
    correct_order: list[str] = Field(min_length=3)
    acceptable_orders: list[list[str]] = []
    explanation: str = Field(min_length=10)
    topic: str = ""


class EmailItem(BaseModel):
    topic: str = ""
    scenario: str = Field(min_length=40)
    recipient: str = Field(min_length=2)
    points: list[str] = Field(min_length=2)


class StudentPost(BaseModel):
    name: str = Field(min_length=2)
    text: str = Field(min_length=20)


class DiscussionItem(BaseModel):
    topic: str = ""
    professor_name: str = Field(min_length=2)
    professor_post: str = Field(min_length=30)
    students: list[StudentPost]


class MCQuestion(BaseModel):
    prompt: str = Field(min_length=8)
    options: list[str] = Field(min_length=4, max_length=4)
    answer: int = Field(ge=0, le=3)
    kind: str = "detail"
    explanation: str = Field(min_length=10)


class CompleteWordsItem(BaseModel):
    topic: str = ""
    text: str = Field(min_length=40)
    blanks: list[str] = Field(min_length=5)


class DailyLifeItem(BaseModel):
    topic: str = ""
    format: str = "text"
    title: str = ""
    text: str = Field(min_length=15)
    questions: list[MCQuestion] = Field(min_length=2)


class AcademicPassageItem(BaseModel):
    topic: str = ""
    title: str = Field(min_length=3)
    passage: str = Field(min_length=100)
    questions: list[MCQuestion] = Field(min_length=3)


class Speaker(BaseModel):
    name: str = ""
    gender: Literal["male", "female"] = "female"


class ListenReplyItem(BaseModel):
    topic: str = ""
    utterance: str = Field(min_length=6)
    options: list[str] = Field(min_length=4, max_length=4)
    answer: int = Field(ge=0, le=3)
    explanation: str = Field(min_length=10)


class ConvLine(BaseModel):
    speaker: int = Field(ge=0, le=1)
    text: str = Field(min_length=2)


class ConversationItem(BaseModel):
    topic: str = ""
    setting: str = Field(min_length=8)
    speakers: list[Speaker] = Field(min_length=2, max_length=2)
    lines: list[ConvLine] = Field(min_length=4)
    questions: list[MCQuestion] = Field(min_length=2)


class MonologueItem(BaseModel):
    """Announcement or academic talk: one speaker."""

    topic: str = ""
    setting: str = Field(min_length=8)
    speaker: Speaker = Speaker()
    text: str = Field(min_length=40)
    questions: list[MCQuestion] = Field(min_length=2)


class RepeatItem(BaseModel):
    topic: str = ""
    sentence: str = Field(min_length=10)


class InterviewItem(BaseModel):
    topic: str = ""
    setting: str = Field(min_length=8)
    interviewer: Speaker = Speaker()
    questions: list[str] = Field(min_length=4, max_length=4)


class SpeakingErrorNote(BaseModel):
    category: Literal["grammar", "vocabulary", "organization", "task_fulfillment", "delivery"]
    quote: str = ""
    issue: str
    fix: str = ""


class SpeakingItemFeedback(BaseModel):
    score: float = Field(ge=0, le=5)
    summary: str = ""
    strengths: list[str] = []
    errors: list[SpeakingErrorNote] = []
    model_answer: str = ""


class SpeakingFeedback(BaseModel):
    items: list[SpeakingItemFeedback]


class WritingErrorNote(BaseModel):
    category: Literal["grammar", "vocabulary", "organization", "task_fulfillment"]
    quote: str = ""
    issue: str
    fix: str = ""


class WritingFeedback(BaseModel):
    score: float = Field(ge=0, le=5)
    summary: str = ""
    strengths: list[str] = []
    errors: list[WritingErrorNote] = []
    model_answer: str = ""


# ---------- API ----------


class CreateAttempt(BaseModel):
    mode: Literal["full", "section", "task", "weak"]
    difficulty: Difficulty
    exam_mode: Literal["exam", "practice"] = "exam"
    timed: bool = True
    section: Section | None = None
    task_type: TaskType | None = None
    task_types: list[TaskType] | None = None  # mode "weak": the task types to drill, possibly from several sections


class TaskInfo(BaseModel):
    task_type: TaskType
    budget_seconds: int
    count: int


class SectionStatus(BaseModel):
    section: Section
    status: str
    band: float | None
    stage: str = "main"
    stage_label: str = ""
    stage_count: int = 1
    route: dict[str, Any] | None = None
    tasks: list[TaskInfo]
    current_task: int
    task_deadline: str | None
    warnings: list[str]
    error: str | None = None


class AttemptOut(BaseModel):
    id: int
    mode: str
    difficulty: Difficulty
    exam_mode: str
    timed: bool
    status: str
    server_now: str
    sections: list[SectionStatus]


class RunItem(BaseModel):
    response_id: int
    position: int
    task_type: TaskType
    prompt: dict[str, Any]
    answer: dict[str, Any] | None
    has_audio: bool = False
    audio_parts: int = 0  # number of audio clips (an interview has one per question)
    audio_played: list[bool] = []  # exam mode: per clip, has the one allowed play been used


class RunOut(BaseModel):
    status: str
    stage: str = "main"
    stage_label: str = ""
    stage_count: int = 1
    server_now: str
    current_task: int
    task_type: TaskType | None
    task_deadline: str | None
    tasks: list[TaskInfo]
    items: list[RunItem]


class SaveAnswer(BaseModel):
    answer: dict[str, Any]


class ReviewItem(BaseModel):
    response_id: int
    task_type: TaskType
    position: int
    prompt: dict[str, Any]
    answer: dict[str, Any] | None
    score: float | None
    max_score: float | None
    feedback: dict[str, Any] | None


class TaskResult(BaseModel):
    stage: str = "main"
    stage_label: str = ""
    level: Difficulty | None = None
    task_type: TaskType
    points: float
    max_points: float
    items: list[ReviewItem]


class SectionResult(BaseModel):
    route: dict[str, Any] | None = None
    section: Section
    status: str
    band: float | None
    points: float | None
    max_points: float | None
    tasks: list[TaskResult]
    error: str | None = None


class ResultsOut(BaseModel):
    attempt_id: int
    difficulty: Difficulty
    mode: str
    status: str
    overall_band: float | None
    disclaimer: str
    sections: list[SectionResult]


class HistoryAttempt(BaseModel):
    id: int
    mode: str
    difficulty: Difficulty
    exam_mode: str
    status: str
    started_at: str
    overall_band: float | None
    bands: dict[str, float | None]  # section -> band for sections that were taken
    tasks: list[str] = []  # task types, for single-task attempts


class HistoryOut(BaseModel):
    attempts: list[HistoryAttempt]  # newest first


class TaskStat(BaseModel):
    task_type: TaskType
    section: Section
    band: float  # level-adjusted estimate, recency weighted (see services/analytics.py)
    last_band: float
    accuracy: float  # fraction of points earned, all time
    attempts: int
    trend: float | None  # latest attempt's band minus the mean of up to 3 earlier ones


class SectionSummary(BaseModel):
    section: Section
    latest: float
    best: float
    average: float
    count: int


class AnalyticsOut(BaseModel):
    attempts_scored: int
    tasks: list[TaskStat]  # weakest first
    weakest: list[TaskType]
    sections: list[SectionSummary]
    error_categories: dict[str, int]  # writing/speaking feedback, recent attempts
    suggested_difficulty: Difficulty | None


class WeakSpotRequest(BaseModel):
    difficulty: Difficulty | None = None  # default: the level of the latest scored attempt
    exam_mode: Literal["exam", "practice"] = "practice"
    timed: bool = True
    count: int = Field(default=3, ge=1, le=5)
