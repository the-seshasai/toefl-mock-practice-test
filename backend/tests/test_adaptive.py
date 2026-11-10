"""Adaptive routing for Reading/Listening and the full four-section test."""
from datetime import timedelta

import pytest
from sqlalchemy import select

from app import spec
from app.db import SessionLocal
from app.models import Attempt, Item, Response, SectionAttempt
from app.scoring.bands import adaptive_band, stage_band
from app.services import exam
from app.spec import Difficulty
from tests.flow import create, play_section


def stage_rows(aid: int, section: str = "reading") -> dict[str, list[tuple[Response, Item]]]:
    out: dict[str, list] = {}
    with SessionLocal() as db:
        sa = db.scalar(select(SectionAttempt).where(SectionAttempt.attempt_id == aid, SectionAttempt.section == section))
        for r, i in db.execute(select(Response, Item).join(Item, Item.id == Response.item_id).where(Response.section_attempt_id == sa.id)):
            out.setdefault(r.stage, []).append((i.id, i.difficulty, i.served, i.source))
    return out


# ---------- routing ----------


def test_strong_router_routes_up_and_unused_module_returns_to_bank(client, clock) -> None:
    aid = create(client, section="reading", difficulty="beginner")["id"]
    before = stage_rows(aid)
    assert set(before) == {"router", "lower", "upper"}  # both candidate modules are prepared in advance
    lower_item_ids = {item_id for item_id, *_ in before["lower"]}
    final = play_section(client, aid, "reading")
    assert final["status"] == "scored"
    after = stage_rows(aid)
    assert set(after) == {"router", "upper"}  # the lower module's responses are gone
    assert {d for _, d, _, _ in after["router"]} == {"beginner"} and {d for _, d, _, _ in after["upper"]} == {"intermediate"}
    with SessionLocal() as db:  # the unused module's generated items are unserved again, so a later exam can use them
        returned = db.scalars(select(Item).where(Item.id.in_(lower_item_ids), Item.source == "generated")).all()
        assert returned and all(not i.served for i in returned)
    res = client.get(f"/api/attempts/{aid}/results").json()["sections"][0]
    assert res["route"] == {"to": "upper", "router_fraction": 1.0, "router_level": "beginner", "module_level": "intermediate"}


def test_weak_router_routes_down(client, clock) -> None:
    aid = create(client, section="reading", difficulty="intermediate")["id"]
    play_section(client, aid, "reading", correct=False)
    res = client.get(f"/api/attempts/{aid}/results").json()["sections"][0]
    assert res["route"]["to"] == "lower" and res["route"]["module_level"] == "beginner" and res["band"] == 1.0
    assert [t["level"] for t in res["tasks"]] == ["intermediate"] * 3 + ["beginner"] * 3


def test_routing_threshold_uses_router_points(client, clock) -> None:
    """Only Complete the Words correct: 20 of 29 router points (0.69) is enough to go up; only the others: 9/29 goes down."""
    up = create(client, section="reading")["id"]
    play_section(client, up, "reading", only={"complete_the_words"})
    down = create(client, section="reading")["id"]
    play_section(client, down, "reading", only={"read_in_daily_life", "read_academic_passage"})
    routes = [client.get(f"/api/attempts/{a}/results").json()["sections"][0]["route"] for a in (up, down)]
    assert [r["to"] for r in routes] == ["upper", "lower"] and routes[0]["router_fraction"] > spec.ROUTE_UP_THRESHOLD > routes[1]["router_fraction"]


def test_levels_clamp_at_the_ends_of_the_ladder() -> None:
    assert spec.route_levels(Difficulty.BEGINNER) == {"lower": Difficulty.BEGINNER, "upper": Difficulty.INTERMEDIATE}
    assert spec.route_levels(Difficulty.ADVANCED) == {"lower": Difficulty.INTERMEDIATE, "upper": Difficulty.ADVANCED}


def test_listening_modules_have_different_lengths(client, clock) -> None:
    up = create(client, section="listening")["id"]
    play_section(client, up, "listening")
    down = create(client, section="listening")["id"]
    play_section(client, down, "listening", correct=False)
    ups = client.get(f"/api/attempts/{up}/results").json()["sections"][0]
    downs = client.get(f"/api/attempts/{down}/results").json()["sections"][0]
    assert ups["route"]["to"] == "upper" and downs["route"]["to"] == "lower"
    sizes = {}
    for name, res in (("upper", ups), ("lower", downs)):
        second = [t for t in res["tasks"] if t["stage_label"] == "Module 2"]
        sizes[name] = sum(len(t["items"]) for t in second)
    assert sizes == {"upper": 9, "lower": 9}  # same number of sets; the upper module just gets more time (11 vs 7 min)
    assert spec.ADAPTIVE_STAGES[spec.Section.LISTENING]["upper"] != spec.ADAPTIVE_STAGES[spec.Section.LISTENING]["lower"]


# ---------- timers across stages ----------


def test_second_module_clock_starts_when_the_router_ends(client, clock) -> None:
    aid = create(client, section="reading")["id"]
    client.post(f"/api/attempts/{aid}/sections/reading/start")
    clock.tick(40)
    for _ in range(3):
        run = client.post(f"/api/attempts/{aid}/sections/reading/advance").json()
    assert run["stage"] == "lower" and run["stage_label"] == "Module 2" and run["task_type"] == "complete_the_words"
    assert run["task_deadline"] == (clock.now() + timedelta(seconds=150)).isoformat()  # Module 2, first task: 2.5 min from now
    assert [t["budget_seconds"] for t in run["tasks"]] == [150, 120, 270]  # 9 minutes


def test_router_expiry_routes_automatically_and_keeps_the_strict_clock(client, clock) -> None:
    aid = create(client, section="reading")["id"]
    client.post(f"/api/attempts/{aid}/sections/reading/start")
    start = clock.now()
    clock.tick(21 * 60 + 10)  # every router task expired while the user was away
    run = client.get(f"/api/attempts/{aid}/sections/reading/run").json()
    assert run["status"] == "in_progress" and run["stage"] == "lower"  # nothing answered -> lower module
    assert run["task_deadline"] == (start + timedelta(seconds=21 * 60 + 150)).isoformat()  # anchored at the router's deadline


def test_answers_for_the_other_stage_are_locked(client, clock) -> None:
    aid = create(client, section="reading")["id"]
    client.post(f"/api/attempts/{aid}/sections/reading/start")
    with SessionLocal() as db:
        module_rid = db.scalars(select(Response.id).where(Response.stage == "upper").order_by(Response.position)).first()
    r = client.put(f"/api/attempts/{aid}/responses/{module_rid}", json={"answer": {"letters": ["a"]}})
    assert r.status_code == 409  # the second module's items cannot be answered during the router


# ---------- waiting for the module / fallbacks ----------


def test_user_waits_when_the_next_module_is_not_ready_yet(client, clock) -> None:
    aid = create(client, section="reading")["id"]
    with SessionLocal() as db:  # simulate "candidate modules still generating"
        sa = db.scalar(select(SectionAttempt).where(SectionAttempt.attempt_id == aid))
        sa.gen = {}
        db.commit()
    client.post(f"/api/attempts/{aid}/sections/reading/start")
    for _ in range(3):
        run = client.post(f"/api/attempts/{aid}/sections/reading/advance").json()
    assert run["status"] == "preparing_next" and run["items"] == [] and run["stage_label"] == "Module 2"
    assert client.get(f"/api/attempts/{aid}").json()["sections"][0]["status"] == "preparing_next"
    clock.tick(30)
    assert client.post(f"/api/attempts/{aid}/sections/reading/submit").json()["status"] == "preparing_next"  # cannot skip the wait
    with SessionLocal() as db:  # the generation job finishes
        sa = db.scalar(select(SectionAttempt).where(SectionAttempt.attempt_id == aid))
        sa.gen = {"candidates_ready": True}
        db.commit()
        exam._try_route(db, db.get(Attempt, aid), sa)
        exam._try_route(db, db.get(Attempt, aid), sa)  # idempotent: a second call must not re-enter the module
    run = client.get(f"/api/attempts/{aid}/sections/reading/run").json()
    assert run["status"] == "in_progress" and run["stage"] == "lower" and run["task_type"] == "complete_the_words"
    assert run["task_deadline"] == (clock.now() + timedelta(seconds=150)).isoformat()  # the module's clock starts when it opens


def test_missing_chosen_module_falls_back_to_the_other(client, clock) -> None:
    aid = create(client, section="reading")["id"]
    with SessionLocal() as db:
        for r in db.scalars(select(Response).where(Response.stage == "upper")):
            db.delete(r)
        db.commit()
    play_section(client, aid, "reading")  # a perfect router would go up, but that module is gone
    res = client.get(f"/api/attempts/{aid}/results").json()["sections"][0]
    assert res["status"] == "scored" and res["route"]["to"] == "lower" and res["route"]["fallback"] is True


def test_section_fails_cleanly_when_neither_module_exists(client, clock) -> None:
    aid = create(client, section="reading")["id"]
    with SessionLocal() as db:
        for r in db.scalars(select(Response).where(Response.stage.in_(["upper", "lower"]))):
            db.delete(r)
        db.commit()
    client.post(f"/api/attempts/{aid}/sections/reading/start")
    for _ in range(3):
        client.post(f"/api/attempts/{aid}/sections/reading/advance")
    sec = client.get(f"/api/attempts/{aid}").json()["sections"][0]
    assert sec["status"] == "failed" and "second module" in sec["error"]


# ---------- band formula ----------


def test_stage_band_intervals() -> None:
    B, I, A = Difficulty.BEGINNER, Difficulty.INTERMEDIATE, Difficulty.ADVANCED
    assert (stage_band("router", I, 0, 10), stage_band("router", I, 10, 10)) == (1.0, 5.0)
    assert (stage_band("upper", I, 0, 10), stage_band("upper", I, 10, 10)) == (3.5, 5.0)  # [ceiling(Beginner), ceiling(Intermediate)]
    assert (stage_band("upper", A, 0, 10), stage_band("upper", A, 10, 10)) == (5.0, 6.0)
    assert (stage_band("lower", B, 0, 10), stage_band("lower", B, 10, 10)) == (1.0, 3.5)
    assert stage_band("router", I, 5, 0) == 1.0


def test_adaptive_band_properties() -> None:
    I, A, B = Difficulty.INTERMEDIATE, Difficulty.ADVANCED, Difficulty.BEGINNER
    # Aced the router, failed the harder module: still at least the router's ceiling, never penalized for being routed up.
    assert adaptive_band([("router", I, 29, 29), ("upper", A, 0, 18)]) == 5.0
    assert adaptive_band([("router", I, 29, 29), ("upper", A, 18, 18)]) == 5.5 or adaptive_band([("router", I, 29, 29), ("upper", A, 18, 18)]) == 5.5
    # Monotonic in points within a fixed route
    for route in (("upper", A), ("lower", B)):
        bands = [adaptive_band([("router", I, 18, 29), (route[0], route[1], p, 18)]) for p in range(19)]
        assert bands == sorted(bands)
    # Doing well in the upper module beats doing equally well in the lower one
    assert adaptive_band([("router", I, 20, 29), ("upper", A, 12, 18)]) > adaptive_band([("router", I, 20, 29), ("lower", B, 12, 18)])
    assert adaptive_band([]) == 1.0


# ---------- full test ----------


def test_full_test_runs_all_four_sections_in_order(client, clock, llm) -> None:
    a = create(client, mode="full", section=None, difficulty="beginner")
    aid = a["id"]
    assert [s["section"] for s in a["sections"]] == ["reading", "listening", "writing", "speaking"]
    assert [s["status"] for s in a["sections"]] == ["ready"] * 4  # later sections were prepared in the background
    assert client.post(f"/api/attempts/{aid}/sections/writing/start").status_code == 409  # no skipping ahead
    assert client.post(f"/api/attempts/{aid}/sections/listening/start").status_code == 409
    for section in ("reading", "listening", "writing", "speaking"):
        assert play_section(client, aid, section)["status"] == "scored"
    res = client.get(f"/api/attempts/{aid}/results").json()
    bands = [s["band"] for s in res["sections"]]
    assert all(b is not None for b in bands) and res["status"] == "complete"
    assert res["overall_band"] == spec.overall_band(bands)
    assert res["overall_band"] % 0.5 == 0
    with SessionLocal() as db:
        assert db.get(Attempt, aid).overall_band == res["overall_band"]


def test_next_section_unlocks_after_the_previous_is_submitted(client, clock) -> None:
    aid = create(client, mode="full", section=None)["id"]
    client.post(f"/api/attempts/{aid}/sections/reading/start")
    assert client.post(f"/api/attempts/{aid}/sections/listening/start").status_code == 409  # reading still in progress
    client.post(f"/api/attempts/{aid}/sections/reading/submit")
    assert client.post(f"/api/attempts/{aid}/sections/listening/start").status_code == 200


def test_one_failing_section_does_not_block_the_others(client, llm, clock) -> None:
    llm.tts.voices = []  # Listening and Speaking need Piper voices; Reading and Writing do not
    a = create(client, mode="full", section=None)
    status = {s["section"]: s["status"] for s in a["sections"]}
    assert status == {"reading": "ready", "listening": "failed", "writing": "ready", "speaking": "failed"}
    assert "Piper voices" in next(s for s in a["sections"] if s["section"] == "listening")["error"]


def test_single_task_mode_stays_non_adaptive(client, clock) -> None:
    a = create(client, mode="task", section=None, task_type="read_academic_passage")
    sec = a["sections"][0]
    assert sec["stage"] == "main" and sec["stage_count"] == 1 and sec["stage_label"] == ""
    assert play_section(client, a["id"], "reading")["status"] == "scored"
    with SessionLocal() as db:
        assert {r.stage for r in db.scalars(select(Response))} == {"main"}


@pytest.mark.parametrize("mode", ["section", "task"])
def test_non_full_modes_have_no_overall_band(client, clock, mode) -> None:
    kw = {"mode": mode, "section": "writing"} if mode == "section" else {"mode": mode, "section": None, "task_type": "write_email"}
    aid = create(client, **kw)["id"]
    play_section(client, aid, "writing")
    assert client.get(f"/api/attempts/{aid}/results").json()["overall_band"] is None
