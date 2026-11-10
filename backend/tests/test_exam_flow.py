from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app import spec
from tests.flow import LONG, correct_answer, create, upload  # noqa: F401


def answer_all(client: TestClient, aid: int, run: dict) -> None:
    for it in run["items"]:
        if run["task_type"] == "build_a_sentence":
            n = it["prompt"]["context"].split()[3]  # helpers.bas_item: context names the student number
            ans = {"order": [f"Student{n}", "reads", "a book", "in the library", "tonight."]}
        else:
            ans = {"text": LONG}
        assert client.put(f"/api/attempts/{aid}/responses/{it['response_id']}", json={"answer": ans}).status_code == 204


def test_full_writing_section_happy_path(client, clock) -> None:
    a = create(client)
    aid = a["id"]
    sec = a["sections"][0]
    assert sec["status"] == "ready" and [t["count"] for t in sec["tasks"]] == [10, 1, 1]
    assert sum(t["budget_seconds"] for t in sec["tasks"]) == 23 * 60
    assert client.get(f"/api/attempts/{aid}/sections/writing/run").json()["items"] == []  # hidden before start

    client.post(f"/api/attempts/{aid}/sections/writing/start")
    run = client.get(f"/api/attempts/{aid}/sections/writing/run").json()
    assert run["task_type"] == "build_a_sentence" and len(run["items"]) == 10
    assert all("correct_order" not in i["prompt"] for i in run["items"])  # answers never leak
    answer_all(client, aid, run)

    run = client.post(f"/api/attempts/{aid}/sections/writing/advance").json()
    assert run["task_type"] == "write_email"
    answer_all(client, aid, run)
    run = client.post(f"/api/attempts/{aid}/sections/writing/advance").json()
    assert run["task_type"] == "write_academic_discussion"
    answer_all(client, aid, run)
    assert client.post(f"/api/attempts/{aid}/sections/writing/submit").json()["status"] == "scored"

    res = client.get(f"/api/attempts/{aid}/results").json()
    s = res["sections"][0]
    assert s["points"] == 10 + 4 + 4 and s["max_points"] == 20
    assert s["band"] == 3.5  # 1 + 2.5 * 0.9 = 3.25 -> half-up to 3.5 at Beginner
    assert "not official" in res["disclaimer"].lower() and res["overall_band"] is None
    email = s["tasks"][1]["items"][0]
    assert email["feedback"]["model_answer"] and email["answer"]["text"] == LONG


def test_timer_expiry_autoadvances_and_locks_answers(client, clock) -> None:
    aid = create(client)["id"]
    client.post(f"/api/attempts/{aid}/sections/writing/start")
    run = client.get(f"/api/attempts/{aid}/sections/writing/run").json()
    first = run["items"][0]["response_id"]
    clock.tick(6 * 60 + 2)  # inside grace: still saveable
    assert client.put(f"/api/attempts/{aid}/responses/{first}", json={"answer": {"order": ["x"]}}).status_code == 204
    clock.tick(5)  # past grace: task 1 locked, email now current
    assert client.put(f"/api/attempts/{aid}/responses/{first}", json={"answer": {"order": ["y"]}}).status_code == 409
    run = client.get(f"/api/attempts/{aid}/sections/writing/run").json()
    assert run["task_type"] == "write_email"
    # next clock started at the previous deadline, not at "now"
    assert run["task_deadline"] == (datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=6 * 60 + 7 * 60)).isoformat()


def test_section_auto_submits_when_everything_expires(client, clock) -> None:
    aid = create(client)["id"]
    client.post(f"/api/attempts/{aid}/sections/writing/start")
    clock.tick(23 * 60 + 10)
    out = client.get(f"/api/attempts/{aid}").json()
    assert out["sections"][0]["status"] == "scored" and out["status"] == "complete"
    res = client.get(f"/api/attempts/{aid}/results").json()
    assert res["sections"][0]["points"] == 0  # nothing answered


def test_practice_untimed_has_no_deadlines(client, clock) -> None:
    aid = create(client, exam_mode="practice", timed=False)["id"]
    client.post(f"/api/attempts/{aid}/sections/writing/start")
    clock.tick(10 * 3600)
    run = client.get(f"/api/attempts/{aid}/sections/writing/run").json()
    assert run["status"] == "in_progress" and run["task_deadline"] is None


def test_single_task_mode(client, clock) -> None:
    a = create(client, mode="task", section=None, task_type="write_email")
    assert [t["task_type"] for t in a["sections"][0]["tasks"]] == ["write_email"]
    aid = a["id"]
    client.post(f"/api/attempts/{aid}/sections/writing/start")
    run = client.get(f"/api/attempts/{aid}/sections/writing/run").json()
    answer_all(client, aid, run)
    assert client.post(f"/api/attempts/{aid}/sections/writing/submit").json()["status"] == "scored"


def test_same_setup_twice_gives_different_questions(client, clock) -> None:
    def prompts() -> list[str]:
        aid = create(client)["id"]
        client.post(f"/api/attempts/{aid}/sections/writing/start")
        return [i["prompt"]["context"] for i in client.get(f"/api/attempts/{aid}/sections/writing/run").json()["items"]]

    assert set(prompts()).isdisjoint(prompts())


def test_generation_failure_uses_fallback_bank_and_warns(client, llm, clock) -> None:
    llm.fail_generation = True
    a = create(client)
    sec = a["sections"][0]
    assert sec["status"] == "ready" and sec["warnings"]


def test_scoring_failure_can_be_retried(client, llm, clock) -> None:
    llm.fail_scoring = True
    aid = create(client)["id"]
    client.post(f"/api/attempts/{aid}/sections/writing/start")
    answer_all(client, aid, client.get(f"/api/attempts/{aid}/sections/writing/run").json())
    client.post(f"/api/attempts/{aid}/sections/writing/advance")
    run = client.get(f"/api/attempts/{aid}/sections/writing/run").json()
    answer_all(client, aid, run)
    client.post(f"/api/attempts/{aid}/sections/writing/advance")
    answer_all(client, aid, client.get(f"/api/attempts/{aid}/sections/writing/run").json())
    client.post(f"/api/attempts/{aid}/sections/writing/submit")
    assert client.get(f"/api/attempts/{aid}").json()["sections"][0]["status"] == "scoring_failed"
    llm.fail_scoring = False
    out = client.post(f"/api/attempts/{aid}/sections/writing/rescore").json()
    assert out["sections"][0]["status"] == "scored" and out["status"] == "complete"


def test_stage_budgets_match_the_blueprint() -> None:
    def minutes(stage: spec.StageTasks) -> int:
        return sum(seconds for _, _, seconds in stage) // 60

    reading, listening = spec.ADAPTIVE_STAGES[spec.Section.READING], spec.ADAPTIVE_STAGES[spec.Section.LISTENING]
    assert minutes(reading[spec.ROUTER]) == 21 and minutes(reading[spec.UPPER]) == minutes(reading[spec.LOWER]) == 9
    assert minutes(listening[spec.ROUTER]) == 18 and minutes(listening[spec.LOWER]) == 7 and minutes(listening[spec.UPPER]) == 11
    for section in (spec.Section.WRITING, spec.Section.SPEAKING):  # linear sections: per-task budgets sum to the section time
        assert sum(spec.TASK_SECONDS[t] for t in spec.SECTION_TASKS[section]) == spec.SECTION_MINUTES[section] * 60


# ---------- Reading section ----------


def test_reading_prompts_never_leak_answers(client, clock) -> None:
    aid = create(client, section="reading")["id"]
    client.post(f"/api/attempts/{aid}/sections/reading/start")
    for _ in range(3):
        run = client.get(f"/api/attempts/{aid}/sections/reading/run").json()
        for it in run["items"]:
            text = str(it["prompt"])
            assert "'answer'" not in text and "explanation" not in text and "'blanks'" not in text
        client.post(f"/api/attempts/{aid}/sections/reading/advance")


def test_reading_section_end_to_end(client, clock) -> None:
    from tests.flow import play_section

    a = create(client, section="reading")
    aid = a["id"]
    sec = a["sections"][0]
    assert sec["status"] == "ready" and sec["stage"] == "router" and sec["stage_label"] == "Module 1" and sec["stage_count"] == 2
    assert [t["count"] for t in sec["tasks"]] == [2, 2, 1] and sum(t["budget_seconds"] for t in sec["tasks"]) == 21 * 60
    final = play_section(client, aid, "reading")
    assert final["status"] == "scored"
    s = client.get(f"/api/attempts/{aid}/results").json()["sections"][0]
    assert s["points"] == s["max_points"] and s["route"]["to"] == "upper" and s["route"]["router_fraction"] == 1.0
    assert [t["stage_label"] for t in s["tasks"]] == ["Module 1"] * 3 + ["Module 2"] * 3
    assert [t["level"] for t in s["tasks"]] == ["beginner"] * 3 + ["intermediate"] * 3  # routed up from Beginner
    mc = s["tasks"][2]["items"][0]
    assert mc["feedback"]["questions"][0]["explanation"] and mc["prompt"]["questions"][0]["answer"] in range(4)
    assert 3.5 < s["band"] <= 5.0  # perfect on Beginner router + Intermediate module


def test_reading_malformed_answers_rejected(client, clock) -> None:
    aid = create(client, section="reading")["id"]
    client.post(f"/api/attempts/{aid}/sections/reading/start")
    rid = client.get(f"/api/attempts/{aid}/sections/reading/run").json()["items"][0]["response_id"]
    assert client.put(f"/api/attempts/{aid}/responses/{rid}", json={"answer": {"letters": "oops"}}).status_code == 400
    assert client.put(f"/api/attempts/{aid}/responses/{rid}", json={"answer": {"letters": ["a"]}}).status_code == 204


def test_reading_unanswered_scores_zero_and_single_task_mode(client, clock) -> None:
    a = create(client, mode="task", section=None, task_type="read_academic_passage", difficulty="intermediate")
    aid = a["id"]
    assert [t["task_type"] for t in a["sections"][0]["tasks"]] == ["read_academic_passage"]
    client.post(f"/api/attempts/{aid}/sections/reading/start")
    client.post(f"/api/attempts/{aid}/sections/reading/submit")
    s = client.get(f"/api/attempts/{aid}/results").json()["sections"][0]
    assert s["points"] == 0 and s["band"] == 1.0 and s["max_points"] > 0


def test_reading_timer_per_task(client, clock) -> None:
    aid = create(client, section="reading")["id"]
    client.post(f"/api/attempts/{aid}/sections/reading/start")
    clock.tick(5 * 60 + 5)  # Complete the Words budget in the router
    run = client.get(f"/api/attempts/{aid}/sections/reading/run").json()
    assert run["task_type"] == "read_in_daily_life" and run["stage"] == "router"


# ---------- Listening section ----------


def test_listening_end_to_end_with_gated_audio(client, clock, llm) -> None:
    from sqlalchemy import select

    from app.db import SessionLocal
    from app.models import Item, Response
    from tests.flow import play_section

    a = create(client, section="listening")
    aid = a["id"]
    sec = a["sections"][0]
    assert sec["status"] == "ready" and sec["stage"] == "router" and [t["count"] for t in sec["tasks"]] == [10, 3, 2, 2]
    assert sum(t["budget_seconds"] for t in sec["tasks"]) == 18 * 60
    assert llm.tts.calls  # audio was synthesized during generation

    with SessionLocal() as db:
        first_rid = db.scalars(select(Response.id).where(Response.stage == "router").order_by(Response.position)).first()
        row = db.get(Item, db.get(Response, first_rid).item_id)
        assert "voice" in row.payload["script"][0] and row.payload["audio_key"]
    assert client.get(f"/api/attempts/{aid}/responses/{first_rid}/audio").status_code == 409  # section not started

    client.post(f"/api/attempts/{aid}/sections/listening/start")
    run = client.get(f"/api/attempts/{aid}/sections/listening/run").json()
    assert run["task_type"] == "listen_choose_response" and len(run["items"]) == 10
    item = run["items"][0]
    assert item["has_audio"] and item["audio_played"] == [False]
    assert "script" not in str(item["prompt"]) and "Would you like" not in str(item["prompt"])  # transcript never leaks

    r = client.get(f"/api/attempts/{aid}/responses/{item['response_id']}/audio")
    assert r.status_code == 200 and r.headers["content-type"] == "audio/wav" and r.content[:4] == b"RIFF"
    assert r.headers["cache-control"] == "no-store"
    assert client.get(f"/api/attempts/{aid}/responses/{item['response_id']}/audio").status_code == 200  # retry window
    clock.tick(9)
    assert client.get(f"/api/attempts/{aid}/responses/{item['response_id']}/audio").status_code == 403  # plays once
    run = client.get(f"/api/attempts/{aid}/sections/listening/run").json()
    assert run["items"][0]["audio_played"] == [True] and run["items"][1]["audio_played"] == [False]

    # audio of a task that is not current is closed
    with SessionLocal() as db:
        conv_rid = db.scalars(select(Response.id).join(Item, Item.id == Response.item_id).where(Item.task_type == "listen_conversation")).first()
    assert client.get(f"/api/attempts/{aid}/responses/{conv_rid}/audio").status_code == 409

    assert play_section(client, aid, "listening")["status"] == "scored"
    s = client.get(f"/api/attempts/{aid}/results").json()["sections"][0]
    assert s["points"] == s["max_points"] and s["route"]["to"] == "upper" and 3.5 < s["band"] <= 5.0
    assert client.get(f"/api/attempts/{aid}/responses/{item['response_id']}/audio").status_code == 200  # open for review
    review = next(t for t in s["tasks"] if t["task_type"] == "listen_conversation")["items"][0]
    assert review["prompt"]["script"][0]["text"] and review["feedback"]["questions"][0]["explanation"]  # transcript shown in review


def test_listening_practice_mode_allows_replays(client, clock) -> None:
    aid = create(client, section="listening", exam_mode="practice", timed=False)["id"]
    client.post(f"/api/attempts/{aid}/sections/listening/start")
    item = client.get(f"/api/attempts/{aid}/sections/listening/run").json()["items"][0]
    for _ in range(3):
        clock.tick(30)
        assert client.get(f"/api/attempts/{aid}/responses/{item['response_id']}/audio").status_code == 200
    assert client.get(f"/api/attempts/{aid}/sections/listening/run").json()["items"][0]["audio_played"] == [False]


def test_listening_without_voices_fails_clearly(client, llm) -> None:
    llm.tts.voices = []
    a = create(client, section="listening")
    sec = a["sections"][0]
    assert sec["status"] == "failed" and "Piper voices" in sec["error"]


def test_listening_falls_back_to_seeds_and_still_builds_audio(client, llm, clock) -> None:
    llm.fail_generation = True
    a = create(client, section="listening", difficulty="intermediate")
    sec = a["sections"][0]
    assert sec["status"] == "ready" and sec["warnings"] and llm.tts.calls


# ---------- Speaking section ----------


def speaking_items(client, aid) -> list[dict]:
    return client.get(f"/api/attempts/{aid}/sections/speaking/run").json()["items"]


def test_speaking_section_end_to_end(client, clock, llm) -> None:
    from sqlalchemy import select

    from app.db import SessionLocal
    from app.models import Item, Response

    a = create(client, section="speaking")
    aid = a["id"]
    sec = a["sections"][0]
    assert sec["status"] == "ready" and [t["count"] for t in sec["tasks"]] == [7, 1]
    assert sum(t["budget_seconds"] for t in sec["tasks"]) == 8 * 60
    client.post(f"/api/attempts/{aid}/sections/speaking/start")

    run = client.get(f"/api/attempts/{aid}/sections/speaking/run").json()
    assert run["task_type"] == "listen_and_repeat" and len(run["items"]) == 7
    with SessionLocal() as db:
        rows = db.execute(select(Response, Item).join(Item, Item.id == Response.item_id).order_by(Response.position)).all()
        lengths = [i.payload["word_count"] for r, i in rows if i.task_type == "listen_and_repeat"]
        sentences = {r.id: i.payload["sentence"] for r, i in rows if i.task_type == "listen_and_repeat"}
    assert lengths == sorted(lengths)  # sentences get longer through the task
    assert all(it["audio_parts"] == 1 and it["audio_played"] == [False] for it in run["items"])
    assert not any(sentence in str(run) for sentence in sentences.values())  # the target sentence never reaches the client

    first = run["items"][0]["response_id"]
    assert client.put(f"/api/attempts/{aid}/responses/{first}", json={"answer": {"text": "x"}}).status_code == 400  # not a text task
    assert upload(client, aid, first, ctype="video/mp4").status_code == 415
    assert upload(client, aid, first, body=b"x").status_code == 400  # too small
    assert upload(client, aid, first, dur=999_000).status_code == 400  # longer than the window
    assert upload(client, aid, first, part=3).status_code == 404
    for it in run["items"]:  # record the 7 sentences; make the transcription match for all but the last
        rid = it["response_id"]
        llm.stt.texts[f"{aid}_{rid}_0.webm".split("_", 1)[1]] = sentences[rid] if rid != run["items"][-1]["response_id"] else "something else entirely"
        assert upload(client, aid, rid).status_code == 204
    assert upload(client, aid, first).status_code == 409  # exam mode: one attempt per response
    assert client.get(f"/api/attempts/{aid}/responses/{first}/recording").status_code == 403  # no playback mid-exam
    assert client.get(f"/api/attempts/{aid}/sections/speaking/run").json()["items"][0]["answer"]["parts"]["0"]["duration_ms"] == 5000

    run = client.post(f"/api/attempts/{aid}/sections/speaking/advance").json()
    assert run["task_type"] == "take_interview" and len(run["items"]) == 1
    item = run["items"][0]
    assert item["audio_parts"] == 4 and item["audio_played"] == [False] * 4 and item["prompt"]["prep_seconds"] == 10
    for part in range(4):
        assert client.get(f"/api/attempts/{aid}/responses/{item['response_id']}/audio?part={part}").status_code == 200
    clock.tick(9)
    assert client.get(f"/api/attempts/{aid}/responses/{item['response_id']}/audio?part=0").status_code == 403  # each question plays once
    assert client.get(f"/api/attempts/{aid}/responses/{item['response_id']}/audio?part=9").status_code == 404
    assert client.get(f"/api/attempts/{aid}/sections/speaking/run").json()["items"][0]["audio_played"] == [True] * 4
    for part in range(4):
        assert upload(client, aid, item["response_id"], part=part, dur=40_000).status_code == 204

    assert client.post(f"/api/attempts/{aid}/sections/speaking/submit").json()["status"] == "scored"
    assert llm.stt.closed >= 1  # the model is released after scoring
    s = client.get(f"/api/attempts/{aid}/results").json()["sections"][0]
    assert s["max_points"] == 55 and s["points"] == 6 * 5 + 4 * 4.0  # 6 perfect repeats, a wrong one, interview 4 x 4.0
    assert s["band"] == 3.0  # 46/55 -> 1 + 2.5 * 0.836 = 3.09 -> 3.0 at Beginner
    repeat = s["tasks"][0]["items"]
    assert repeat[-1]["score"] == 0.0 and repeat[-1]["feedback"]["differences"] and repeat[0]["feedback"]["delivery"]["wpm"] > 0
    assert s["tasks"][1]["items"][0]["feedback"]["items"][0]["transcript"]
    assert client.get(f"/api/attempts/{aid}/responses/{first}/recording").status_code == 200  # playback after the section ends
    with SessionLocal() as db:
        assert db.get(Response, first).transcript


def test_speaking_practice_mode_allows_rerecording_and_playback(client, clock) -> None:
    aid = create(client, section="speaking", exam_mode="practice", timed=False)["id"]
    client.post(f"/api/attempts/{aid}/sections/speaking/start")
    rid = speaking_items(client, aid)[0]["response_id"]
    assert upload(client, aid, rid, body=b"a" * 300).status_code == 204
    assert upload(client, aid, rid, body=b"b" * 300).status_code == 204  # re-record
    r = client.get(f"/api/attempts/{aid}/responses/{rid}/recording")
    assert r.status_code == 200 and r.content == b"b" * 300  # playback during practice


def test_recordings_lock_when_time_is_up(client, clock) -> None:
    aid = create(client, section="speaking")["id"]
    client.post(f"/api/attempts/{aid}/sections/speaking/start")
    rid = speaking_items(client, aid)[0]["response_id"]
    clock.tick(3 * 60 + 5)  # past the Listen-and-Repeat budget and grace
    assert upload(client, aid, rid).status_code == 409


def test_speaking_scoring_failures_can_be_retried(client, llm, clock) -> None:
    aid = create(client, section="speaking")["id"]
    client.post(f"/api/attempts/{aid}/sections/speaking/start")
    rid = speaking_items(client, aid)[0]["response_id"]
    upload(client, aid, rid)
    llm.stt.fail = True
    client.post(f"/api/attempts/{aid}/sections/speaking/submit")
    assert client.get(f"/api/attempts/{aid}").json()["sections"][0]["status"] == "scoring_failed"
    res = client.get(f"/api/attempts/{aid}/results").json()["sections"][0]
    assert res["band"] is None and "model exploded" in str(res["tasks"][0]["items"][0]["feedback"])
    llm.stt.fail = False
    assert client.post(f"/api/attempts/{aid}/sections/speaking/rescore").json()["sections"][0]["status"] == "scored"


def test_speaking_interview_llm_failure_keeps_repeat_scores(client, llm, clock) -> None:
    aid = create(client, section="speaking")["id"]
    client.post(f"/api/attempts/{aid}/sections/speaking/start")
    for it in speaking_items(client, aid):
        upload(client, aid, it["response_id"])
    client.post(f"/api/attempts/{aid}/sections/speaking/advance")
    iid = speaking_items(client, aid)[0]["response_id"]
    for part in range(4):
        upload(client, aid, iid, part=part, dur=40_000)
    llm.fail_scoring = True
    client.post(f"/api/attempts/{aid}/sections/speaking/submit")
    assert client.get(f"/api/attempts/{aid}").json()["sections"][0]["status"] == "scoring_failed"
    llm.fail_scoring = False
    assert client.post(f"/api/attempts/{aid}/sections/speaking/rescore").json()["sections"][0]["status"] == "scored"
