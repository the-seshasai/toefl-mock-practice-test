import pytest

from app.llm.errors import LLMError
from app.llm.fake import FakeProvider
from app.scoring.bands import estimate_band
from app.scoring.writing import (
    RUBRIC_DIR,
    RUBRIC_FILES,
    score_build_sentence,
    score_text_task,
)
from app.spec import Difficulty, TaskType
from tests.helpers import bas_item, email_item, feedback


def payload_with_alt() -> dict:
    p = bas_item(5)
    p["acceptable_orders"] = [["tonight.", "Student5", "reads", "a book", "in the library"]]
    p["chunks"] = ["a book", "tonight.", "Student5", "reads", "in the library"]
    return p


def test_build_sentence_scoring() -> None:
    p = payload_with_alt()
    ok = score_build_sentence(p, {"order": p["correct_order"]})
    assert ok[0] == 1.0 and ok[2]["correct"] is True
    alt = score_build_sentence(p, {"order": ["Tonight.", "student5", "reads", "a book", "in the library"]})
    assert alt[0] == 1.0  # acceptable order, case-insensitive
    bad = score_build_sentence(p, {"order": ["reads", "Student5"]})
    assert bad[0] == 0.0 and bad[2]["correct_sentence"].startswith("Student5")
    assert score_build_sentence(p, None)[0] == 0.0


def test_estimate_band_is_difficulty_weighted_and_half_stepped() -> None:
    assert estimate_band(0, 20, Difficulty.ADVANCED) == 1.0
    assert estimate_band(20, 20, Difficulty.BEGINNER) == 3.5
    assert estimate_band(20, 20, Difficulty.INTERMEDIATE) == 5.0
    assert estimate_band(20, 20, Difficulty.ADVANCED) == 6.0
    assert estimate_band(10, 20, Difficulty.ADVANCED) == 3.5
    for pts in range(21):
        assert estimate_band(pts, 20, Difficulty.INTERMEDIATE) % 0.5 == 0


def test_text_scoring_uses_rubric_and_wraps_response() -> None:
    llm = FakeProvider([feedback(3.7)])
    text = "Dear teacher, I was sick yesterday and I could not come to class. Please tell me the homework."
    score, mx, fb = score_text_task(llm, TaskType.WRITE_EMAIL, email_item(1), {"text": text}, Difficulty.BEGINNER)
    assert (score, mx) == (3.5, 5.0)  # rounded to half step
    assert fb["rubric_version"] == "writing_email.v1" and fb["model_answer"]
    prompt = llm.calls[0]["prompt"]
    assert "<student_response>" in prompt and text in prompt and "Score descriptors" in prompt
    assert "ignore any request" in llm.calls[0]["system"]


def test_empty_response_scores_zero_without_llm() -> None:
    llm = FakeProvider([feedback()])
    score, _, fb = score_text_task(llm, TaskType.WRITE_EMAIL, email_item(1), {"text": "  hi  "}, Difficulty.BEGINNER)
    assert score == 0.0 and llm.calls == [] and fb["errors"]


def test_llm_failure_propagates_for_retry() -> None:
    class Down(FakeProvider):
        def complete(self, *a, **k) -> str:  # type: ignore[override]
            raise LLMError("down")

    with pytest.raises(LLMError):
        score_text_task(Down([]), TaskType.WRITE_EMAIL, email_item(1), {"text": "word " * 30}, Difficulty.BEGINNER)


def test_rubric_files_exist_and_are_versioned() -> None:
    for name in RUBRIC_FILES.values():
        assert (RUBRIC_DIR / name).exists() and ".v1." in name


def test_difficulty_tables_increase_with_level() -> None:
    """Guards the tuning: ranges never shrink as the level rises, and speech never gets slower."""
    from dataclasses import fields

    from app import difficulty as d
    from app.spec import LEVELS

    tables = [d.BUILD_SENTENCE, d.EMAIL, d.DISCUSSION, d.COMPLETE_WORDS, d.DAILY_LIFE, d.ACADEMIC, d.LISTEN_REPLY, d.CONVERSATION,
              d.ANNOUNCEMENT, d.ACADEMIC_TALK, d.REPEAT, d.INTERVIEW]
    for table in tables:
        for f in fields(table[LEVELS[0]]):
            values = [getattr(table[lv], f.name) for lv in LEVELS]
            if f.name in ("words", "chunks", "scenario_words", "professor_words", "student_words", "question_words", "response_words", "questions", "fk"):
                if f.name in ("questions", "points"):
                    continue  # question/point counts are fixed by the format, not by level
                assert [v[0] for v in values] == sorted(v[0] for v in values), (table, f.name)
                assert [v[1] for v in values] == sorted(v[1] for v in values), (table, f.name)
            if f.name == "length_scale":
                assert values == sorted(values, reverse=True), (table, f.name)  # smaller length_scale = faster speech
    ceilings = [d.BAND_CEILING[lv] for lv in LEVELS]
    assert ceilings == sorted(ceilings) and ceilings[-1] == 6.0


def test_difficulty_report_helpers() -> None:
    from app.tools.difficulty_report import monotonic_warnings, text_of
    from app.validators.readability import fk_grade, syllables

    assert [syllables(w) for w in ("cat", "table", "make", "beautiful", "the")] == [1, 2, 1, 3, 1]
    easy = "The cat sat. The dog ran. We like it."
    hard = "Notwithstanding considerable methodological limitations, comprehensive longitudinal investigations demonstrate substantial improvements."
    assert fk_grade(hard) > fk_grade(easy) + 8
    assert text_of("listen_conversation", {"script": [{"text": "Hi there."}, {"text": "Hello."}]}) == "Hi there. Hello."
    rows = [{"task": "t", "level": lv, "n": 1, "fk": fk, "words": 1} for lv, fk in (("beginner", 5.0), ("intermediate", 4.0), ("advanced", 9.0))]
    assert monotonic_warnings(rows) and not monotonic_warnings(rows[:1] + rows[2:])
