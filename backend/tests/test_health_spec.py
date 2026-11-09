from fastapi.testclient import TestClient

from app import spec
from app.main import app


def test_health() -> None:
    with TestClient(app) as c:
        r = c.get("/api/health")
    assert r.status_code == 200
    assert r.json()["sections"] == ["reading", "listening", "writing", "speaking"]


def test_overall_band_rounds_to_half() -> None:
    assert spec.overall_band([5, 5, 5, 5.5]) == 5.0  # 5.125 -> 5.0 (ETS example)
    assert spec.overall_band([6, 6, 6, 6]) == 6.0
    assert spec.round_band(0.2) == 1.0


def test_task_counts_match_official_totals() -> None:
    assert spec.WRITING_BUILD_SENTENCE_ITEMS + spec.WRITING_EMAIL_ITEMS + spec.WRITING_DISCUSSION_ITEMS == spec.SECTION_ITEMS[spec.Section.WRITING]
    assert spec.SPEAKING_REPEAT_ITEMS + spec.SPEAKING_INTERVIEW_ITEMS == spec.SECTION_ITEMS[spec.Section.SPEAKING]
