"""Progress analytics and the "practice my weak spots" session."""
import pytest

from app import spec
from tests.flow import create, play_section


def analytics(client) -> dict:
    r = client.get("/api/analytics")
    assert r.status_code == 200, r.text
    return r.json()


def by_task(data: dict) -> dict[str, dict]:
    return {t["task_type"]: t for t in data["tasks"]}


def play_reading_strong_in_cloze_only(client) -> int:
    aid = create(client, section="reading", difficulty="beginner")["id"]
    play_section(client, aid, "reading", only={"complete_the_words"})
    return aid


def test_empty_analytics(client) -> None:
    data = analytics(client)
    assert data == {"attempts_scored": 0, "tasks": [], "weakest": [], "sections": [], "error_categories": {}, "suggested_difficulty": None}


def test_weakest_task_types_are_ranked_by_level_adjusted_band(client, clock) -> None:
    play_reading_strong_in_cloze_only(client)
    data = analytics(client)
    stats = by_task(data)
    # Cloze: 20/20 at the Beginner router (band 3.5), 10/10 in the Intermediate module (5.0): (20*3.5 + 10*5.0) / 30 = 4.0
    assert stats["complete_the_words"]["band"] == 4.0 and stats["complete_the_words"]["accuracy"] == 1.0
    # Daily life: 0/4 router (1.0) and 0/3 module (floor 3.5): (4*1 + 3*3.5) / 7 = 2.07. The passage is (5*1 + 6*3.5) / 11 = 2.36
    # here, because the Intermediate module falls back to the 6-question seed passage when the fake LLM's items are too short.
    assert stats["read_in_daily_life"]["band"] == pytest.approx(2.07, abs=0.01)
    assert 2.2 < stats["read_academic_passage"]["band"] < 2.5
    assert [t["task_type"] for t in data["tasks"]] == ["read_in_daily_life", "read_academic_passage", "complete_the_words"]  # weakest first
    assert data["weakest"] == ["read_in_daily_life", "read_academic_passage", "complete_the_words"]
    assert data["attempts_scored"] == 1 and data["suggested_difficulty"] == "beginner"
    assert all(t["section"] == "reading" and t["attempts"] == 1 and t["trend"] is None for t in data["tasks"])


def test_recency_weighting_and_trend(client, clock) -> None:
    first = create(client, section="writing", difficulty="beginner")["id"]
    play_section(client, first, "writing", correct=False)  # nothing answered: every Writing task scores 0
    second = create(client, section="writing", difficulty="beginner")["id"]
    play_section(client, second, "writing")
    stats = by_task(analytics(client))
    # Build a Sentence: latest attempt 10/10 -> 3.5, earlier 0/10 -> 1.0; weights 1 and 0.8 -> (3.5 + 0.8) / 1.8 = 2.39
    bas = stats["build_a_sentence"]
    assert bas["last_band"] == 3.5 and bas["band"] == pytest.approx(2.39, abs=0.01) and bas["attempts"] == 2
    assert bas["trend"] == 2.5  # improved by 2.5 bands over the earlier attempt
    assert bas["accuracy"] == 0.5


def test_levels_count_for_more_when_harder(client, clock) -> None:
    easy = create(client, section="writing", difficulty="beginner")["id"]
    play_section(client, easy, "writing")
    hard = create(client, section="writing", difficulty="advanced")["id"]
    play_section(client, hard, "writing")
    email = by_task(analytics(client))["write_email"]
    # Same 4/5 score: 1 + 2.5*0.8 = 3.0 at Beginner, 1 + 5*0.8 = 5.0 at Advanced. Latest (Advanced) weighs 1, earlier 0.8.
    assert email["last_band"] == 5.0 and email["band"] == pytest.approx((5.0 + 0.8 * 3.0) / 1.8, abs=0.01)


def test_unscored_and_failed_sections_are_ignored(client, llm, clock) -> None:
    create(client, section="writing")  # never taken
    llm.fail_scoring = True
    failed = create(client, section="writing")["id"]
    play_section(client, failed, "writing")
    assert client.get(f"/api/attempts/{failed}").json()["sections"][0]["status"] == "scoring_failed"
    assert analytics(client)["tasks"] == [] and analytics(client)["attempts_scored"] == 0


def test_section_summaries_only_count_whole_section_attempts(client, clock) -> None:
    section_attempt = create(client, section="writing")["id"]
    play_section(client, section_attempt, "writing")
    task_attempt = create(client, mode="task", section=None, task_type="write_email")["id"]
    play_section(client, task_attempt, "writing")
    data = analytics(client)
    writing = next(s for s in data["sections"] if s["section"] == "writing")
    assert writing["count"] == 1 and writing["latest"] == writing["best"] == writing["average"]
    assert data["attempts_scored"] == 2  # but the task attempt still feeds the per-task statistics
    assert by_task(data)["write_email"]["attempts"] == 2


def test_error_categories_come_from_writing_feedback(client, clock) -> None:
    aid = create(client, section="writing")["id"]
    play_section(client, aid, "writing")
    assert analytics(client)["error_categories"] == {"grammar": 2}  # one error note each for the email and the discussion


# ---------- practice my weak spots ----------


def test_weak_spots_needs_history(client) -> None:
    r = client.post("/api/practice/weak-spots", json={})
    assert r.status_code == 400 and "scored practice" in r.json()["detail"]


def test_weak_spot_session_targets_the_weakest_tasks_only(client, clock) -> None:
    play_reading_strong_in_cloze_only(client)
    r = client.post("/api/practice/weak-spots", json={"count": 2, "exam_mode": "practice", "timed": False})
    assert r.status_code == 200, r.text
    a = r.json()
    assert a["mode"] == "weak" and a["difficulty"] == "beginner" and a["exam_mode"] == "practice" and a["timed"] is False
    assert len(a["sections"]) == 1
    sec = a["sections"][0]
    # the two weakest are daily life and the passage; official task order is kept, and it is not adaptive
    assert [t["task_type"] for t in sec["tasks"]] == ["read_in_daily_life", "read_academic_passage"]
    assert sec["stage"] == "main" and sec["stage_count"] == 1 and sec["status"] == "ready"
    assert [t["count"] for t in sec["tasks"]] == [spec.TASK_ITEM_COUNT[spec.TaskType.READ_DAILY_LIFE], spec.TASK_ITEM_COUNT[spec.TaskType.READ_ACADEMIC]]
    assert play_section(client, a["id"], "reading")["status"] == "scored"
    results = client.get(f"/api/attempts/{a['id']}/results").json()
    assert results["overall_band"] is None and [t["task_type"] for t in results["sections"][0]["tasks"]] == ["read_in_daily_life", "read_academic_passage"]


def test_weak_spot_session_can_span_sections_in_exam_order(client, clock) -> None:
    play_reading_strong_in_cloze_only(client)
    writing = create(client, section="writing")["id"]
    play_section(client, writing, "writing")
    data = analytics(client)
    assert data["weakest"] == ["read_in_daily_life", "read_academic_passage", "write_academic_discussion"]  # ties break by name
    a = client.post("/api/practice/weak-spots", json={"difficulty": "intermediate", "exam_mode": "exam"}).json()
    assert a["difficulty"] == "intermediate" and a["timed"] is True
    assert [s["section"] for s in a["sections"]] == ["reading", "writing"]
    assert [[t["task_type"] for t in s["tasks"]] for s in a["sections"]] == [
        ["read_in_daily_life", "read_academic_passage"], ["write_academic_discussion"]]
    assert client.post(f"/api/attempts/{a['id']}/sections/writing/start").status_code == 409  # exam order is enforced
    for section in ("reading", "writing"):
        assert play_section(client, a["id"], section)["status"] == "scored"
    history = client.get("/api/history").json()["attempts"]
    row = next(h for h in history if h["id"] == a["id"])
    assert row["mode"] == "weak" and row["tasks"] == ["read_in_daily_life", "read_academic_passage", "write_academic_discussion"]


def test_weak_spot_request_validation(client, clock) -> None:
    play_reading_strong_in_cloze_only(client)
    assert client.post("/api/practice/weak-spots", json={"count": 9}).status_code == 422
    assert client.post("/api/practice/weak-spots", json={"count": 0}).status_code == 422
    assert client.post("/api/attempts", json={"mode": "weak", "difficulty": "beginner"}).status_code == 400  # no task_types


def test_history_lists_task_types_for_single_task_attempts(client, clock) -> None:
    aid = create(client, mode="task", section=None, task_type="write_email")["id"]
    play_section(client, aid, "writing")
    row = client.get("/api/history").json()["attempts"][0]
    assert row["mode"] == "task" and row["tasks"] == ["write_email"]
