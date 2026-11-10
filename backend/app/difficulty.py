"""Per-task difficulty tables. Difficulty is encoded here, never as ad-hoc prompt wording."""
from dataclasses import dataclass

from app.spec import Difficulty

Range = tuple[int, int]

# Best band a perfect score can reach at each starting level (estimate; see DECISIONS D-06).
BAND_CEILING: dict[Difficulty, float] = {
    Difficulty.BEGINNER: 3.5, Difficulty.INTERMEDIATE: 5.0, Difficulty.ADVANCED: 6.0,
}


@dataclass(frozen=True)
class BuildSentenceParams:
    words: Range
    chunks: Range
    grammar: str
    vocabulary: str
    structures: tuple[str, ...]


@dataclass(frozen=True)
class EmailParams:
    scenario_words: Range
    points: Range
    register: str
    vocabulary: str
    response_words: Range


@dataclass(frozen=True)
class DiscussionParams:
    professor_words: Range
    student_words: Range
    vocabulary: str
    stance: str
    response_words: Range


@dataclass(frozen=True)
class CompleteWordsParams:
    words: Range
    vocabulary: str
    blanks: int


@dataclass(frozen=True)
class DailyLifeParams:
    words: Range
    questions: Range
    vocabulary: str
    formats: tuple[str, ...]
    inference_depth: str
    distractors: str


@dataclass(frozen=True)
class AcademicParams:
    words: Range
    questions: Range
    vocabulary: str
    inference_depth: str
    distractors: str
    fk: tuple[float, float]  # enforced Flesch-Kincaid grade range (tuned from measured output, D-25)
    sentence_words: int  # average sentence length the prompt asks for


@dataclass(frozen=True)
class ListenReplyParams:
    words: Range
    vocabulary: str
    distractors: str
    length_scale: float  # Piper: >1 slower, <1 faster


@dataclass(frozen=True)
class ConversationParams:
    words: Range
    questions: Range
    vocabulary: str
    inference_depth: str
    distractors: str
    length_scale: float


@dataclass(frozen=True)
class MonologueParams:
    words: Range
    questions: Range
    vocabulary: str
    inference_depth: str
    distractors: str
    length_scale: float


@dataclass(frozen=True)
class RepeatParams:
    words: Range  # shortest and longest sentence; an exam spreads its 7 sentences across this range
    vocabulary: str
    structures: str
    length_scale: float
    base_seconds: float  # response window = base + per_word * words
    per_word_seconds: float


@dataclass(frozen=True)
class InterviewParams:
    question_words: Range
    vocabulary: str
    depth: str
    length_scale: float
    prep_seconds: int
    response_seconds: int


BUILD_SENTENCE: dict[Difficulty, BuildSentenceParams] = {
    Difficulty.BEGINNER: BuildSentenceParams(
        (6, 9), (4, 6), "single clause, basic tenses", "common everyday words (CEFR A1-A2)",
        ("a simple present statement", "a simple past statement", "a present continuous statement",
         "a statement with 'because'", "a statement with 'can' or 'must'", "a question with do/does"),
    ),
    Difficulty.INTERMEDIATE: BuildSentenceParams(
        (9, 13), (5, 8), "subordinate clauses, modals, simple passives", "general academic and daily vocabulary (B1-B2)",
        ("a sentence with an embedded that-clause", "a first or second conditional", "a passive sentence",
         "a sentence with a relative clause", "a comparative sentence", "a question with an auxiliary and infinitive phrase"),
    ),
    Difficulty.ADVANCED: BuildSentenceParams(
        (12, 18), (7, 10), "complex embedding, participial phrases, inversion", "academic and idiomatic vocabulary (C1-C2)",
        ("a sentence with a reduced relative clause", "inversion after a negative adverb", "a cleft sentence",
         "a sentence with a participial phrase", "a mixed conditional", "an indirect question embedded in a statement"),
    ),
}

EMAIL: dict[Difficulty, EmailParams] = {
    Difficulty.BEGINNER: EmailParams((25, 50), (2, 3), "informal to polite, simple requests", "common everyday words", (50, 80)),
    Difficulty.INTERMEDIATE: EmailParams((45, 85), (3, 4), "polite semi-formal with some complication", "general academic vocabulary", (80, 120)),
    Difficulty.ADVANCED: EmailParams((60, 110), (3, 4), "formal, requires diplomacy, persuasion or negotiation", "precise academic vocabulary", (110, 160)),
}

DISCUSSION: dict[Difficulty, DiscussionParams] = {
    Difficulty.BEGINNER: DiscussionParams((25, 70), (20, 55), "common words", "clear, concrete everyday-campus opinion question", (60, 90)),
    Difficulty.INTERMEDIATE: DiscussionParams((45, 100), (30, 80), "general academic words", "debatable policy or social question", (100, 140)),
    Difficulty.ADVANCED: DiscussionParams((60, 130), (40, 100), "precise academic words", "abstract or nuanced question needing evaluation of trade-offs", (130, 180)),
}




COMPLETE_WORDS: dict[Difficulty, CompleteWordsParams] = {
    Difficulty.BEGINNER: CompleteWordsParams((50, 75), "common everyday and basic academic words (B1)", 10),
    Difficulty.INTERMEDIATE: CompleteWordsParams((65, 95), "general academic vocabulary (B2)", 10),
    Difficulty.ADVANCED: CompleteWordsParams((80, 115), "formal academic vocabulary, some low-frequency words (C1)", 10),
}

DAILY_LIFE_FORMATS = ("a notice", "an email", "a menu", "an advertisement", "a schedule", "a text-message chat",
                      "a social media post", "a sign or flyer", "a short announcement from a school office")

DAILY_LIFE: dict[Difficulty, DailyLifeParams] = {
    Difficulty.BEGINNER: DailyLifeParams(
        (20, 60), (2, 3), "very common words (A1-A2), short sentences", DAILY_LIFE_FORMATS,
        "answers are stated directly; at most one simple inference", "distractors are clearly wrong on a quick check"),
    Difficulty.INTERMEDIATE: DailyLifeParams(
        (45, 110), (2, 3), "everyday vocabulary with some idioms (B1-B2)", DAILY_LIFE_FORMATS,
        "one question needs a simple inference", "distractors reuse words from the text but misstate the facts"),
    Difficulty.ADVANCED: DailyLifeParams(
        (80, 170), (2, 3), "idiomatic, implicit or telegraphic language (B2-C1)", DAILY_LIFE_FORMATS,
        "at least one question requires reading between the lines", "distractors are plausible and partly supported by the text"),
}

ACADEMIC: dict[Difficulty, AcademicParams] = {
    Difficulty.BEGINNER: AcademicParams(
        (110, 170), (5, 6), "mostly common words; technical terms are explained (B1)",
        "most answers are directly stated; one simple inference", "distractors are clearly wrong on a careful read", (0.0, 9.5), 12),
    Difficulty.INTERMEDIATE: AcademicParams(
        (160, 230), (5, 6), "general academic vocabulary (B2)",
        "two questions need inference or idea relationships", "distractors reuse text wording but distort meaning", (7.0, 12.5), 16),
    Difficulty.ADVANCED: AcademicParams(
        (220, 320), (5, 6), "dense academic vocabulary and abstract ideas (C1-C2)",
        "several questions need inference, rhetorical purpose or cross-paragraph reasoning",
        "distractors are plausible, partly true, and require careful elimination", (12.0, 20.0), 22),
}

LISTEN_REPLY: dict[Difficulty, ListenReplyParams] = {
    Difficulty.BEGINNER: ListenReplyParams((3, 9), "very common words, clear direct meaning (A1-A2)",
                                           "wrong replies answer a different question or are clearly off-topic", 1.15),
    Difficulty.INTERMEDIATE: ListenReplyParams((5, 13), "everyday phrases and some idioms (B1)",
                                               "wrong replies sound plausible but misread the speaker's intent", 1.0),
    Difficulty.ADVANCED: ListenReplyParams((8, 18), "idiomatic, indirect or polite-but-implicit language (B2-C1)",
                                           "wrong replies are grammatical and socially plausible; only one fits the implied meaning", 0.92),
}

CONVERSATION: dict[Difficulty, ConversationParams] = {
    Difficulty.BEGINNER: ConversationParams((40, 90), (2, 3), "simple everyday campus language (A2)",
                                            "answers are stated directly", "distractors are clearly wrong", 1.15),
    Difficulty.INTERMEDIATE: ConversationParams((70, 130), (2, 3), "everyday campus language with some idioms (B1-B2)",
                                                "one question needs a simple inference", "distractors reuse words from the talk but misstate facts", 1.0),
    Difficulty.ADVANCED: ConversationParams((100, 180), (2, 3), "natural, idiomatic, implicit speech (B2-C1)",
                                            "questions about attitude, intent or what a speaker implies", "distractors are plausible and partly supported", 0.92),
}

ANNOUNCEMENT: dict[Difficulty, MonologueParams] = {
    Difficulty.BEGINNER: MonologueParams((45, 95), (2, 3), "simple campus vocabulary (A2)",
                                         "answers are stated directly", "distractors are clearly wrong", 1.15),
    Difficulty.INTERMEDIATE: MonologueParams((80, 150), (2, 3), "campus and administrative vocabulary (B1-B2)",
                                             "one question needs a simple inference", "distractors reuse words but misstate details", 1.0),
    Difficulty.ADVANCED: MonologueParams((120, 210), (2, 3), "administrative language with conditions and exceptions (B2-C1)",
                                         "questions about implications, conditions and reasons", "distractors are plausible and partly supported", 0.92),
}

ACADEMIC_TALK: dict[Difficulty, MonologueParams] = {
    Difficulty.BEGINNER: MonologueParams((90, 150), (3, 5), "mostly common words; terms are explained (B1)",
                                         "most answers are stated directly", "distractors are clearly wrong", 1.15),
    Difficulty.INTERMEDIATE: MonologueParams((140, 210), (3, 5), "general academic vocabulary (B2)",
                                             "two questions need inference or idea relationships", "distractors reuse the speaker's wording but distort it", 1.0),
    Difficulty.ADVANCED: MonologueParams((190, 270), (3, 5), "dense academic vocabulary and abstract ideas (C1-C2)",
                                         "several questions need inference, purpose or organization", "distractors are plausible, partly true", 0.92),
}

REPEAT: dict[Difficulty, RepeatParams] = {
    Difficulty.BEGINNER: RepeatParams((4, 10), "very common words (A1-A2)", "short simple statements and questions, one clause", 1.15, 6.0, 0.6),
    Difficulty.INTERMEDIATE: RepeatParams((7, 16), "everyday and campus vocabulary (B1-B2)", "compound sentences, simple subordinate clauses, modals", 1.0, 6.0, 0.5),
    Difficulty.ADVANCED: RepeatParams((10, 24), "academic and idiomatic vocabulary (C1)", "relative clauses, conditionals, passives, complex noun phrases", 0.92, 6.0, 0.45),
}

INTERVIEW: dict[Difficulty, InterviewParams] = {
    Difficulty.BEGINNER: InterviewParams((6, 16), "everyday words (A2)", "personal, concrete questions; opinions about familiar things", 1.15, 10, 45),
    Difficulty.INTERMEDIATE: InterviewParams((8, 22), "general academic and campus words (B1-B2)", "explanations, comparisons and simple predictions", 1.0, 10, 45),
    Difficulty.ADVANCED: InterviewParams((10, 30), "abstract and academic words (C1)", "evaluation, trade-offs and hypothetical situations", 0.92, 10, 45),
}
