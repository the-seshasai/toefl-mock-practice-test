"""Helpers for driving whole exams through the HTTP API in tests."""
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Item, Response

LONG = " ".join(["word"] * 60)


class Clock:
    def __init__(self) -> None:
        self.t = datetime(2026, 1, 1, tzinfo=UTC)

    def now(self) -> datetime:
        return self.t

    def tick(self, seconds: float) -> None:
        self.t += timedelta(seconds=seconds)


def create(client: TestClient, **kw: Any) -> dict:
    body = {"mode": "section", "section": "writing", "difficulty": "beginner", "exam_mode": "exam", **kw}
    r = client.post("/api/attempts", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def payload_of(response_id: int) -> dict:
    with SessionLocal() as db:
        return db.scalar(select(Item).join(Response, Response.item_id == Item.id).where(Response.id == response_id)).payload


def correct_answer(task_type: str, payload: dict) -> dict:
    if task_type == "build_a_sentence":
        return {"order": payload["correct_order"]}
    if task_type in ("write_email", "write_academic_discussion"):
        return {"text": LONG}
    if task_type == "complete_the_words":
        return {"letters": [b["answer"][len(b["prefix"]):] for b in payload["blanks"]]}
    return {"choices": [q["answer"] for q in payload["questions"]]}


def upload(client: TestClient, aid: int, rid: int, part: int = 0, body: bytes = b"x" * 400, ctype: str = "audio/webm", dur: int = 5000):
    return client.post(f"/api/attempts/{aid}/responses/{rid}/recording?part={part}&duration_ms={dur}", content=body,
                       headers={"content-type": ctype})


def answer_task(client: TestClient, aid: int, run: dict, *, correct: bool = True) -> None:
    """Answer every item of the current task (correctly, or leave blank)."""
    for it in run["items"]:
        if run["task_type"] in ("listen_and_repeat", "take_interview"):
            for part in range(it["audio_parts"]):
                assert upload(client, aid, it["response_id"], part, dur=9000).status_code == 204
        elif correct:
            answer = correct_answer(run["task_type"], payload_of(it["response_id"]))
            assert client.put(f"/api/attempts/{aid}/responses/{it['response_id']}", json={"answer": answer}).status_code == 204


def play_section(client: TestClient, aid: int, section: str, *, correct: bool = True, only: set[str] | None = None) -> dict:
    """Start a section and work through every task of every stage. `only` limits correct answers to those task types."""
    assert client.post(f"/api/attempts/{aid}/sections/{section}/start").status_code == 200
    run = client.get(f"/api/attempts/{aid}/sections/{section}/run").json()
    guard = 0
    while run["status"] == "in_progress":
        guard += 1
        assert guard < 40, "section did not finish"
        answer_task(client, aid, run, correct=correct and (only is None or run["task_type"] in only))
        run = client.post(f"/api/attempts/{aid}/sections/{section}/advance").json()
    return run
