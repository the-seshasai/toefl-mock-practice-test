"""Attempt lifecycle: create -> generate -> start -> per-task timers -> submit -> score -> results."""
import copy
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import spec
from app.audio.builder import AudioBuilder, script_key
from app.audio.parts import audio_parts
from app.audio.stt import SttError
from app.audio.voices import assign_script_voices
from app.config import settings
from app.db import SessionLocal
from app.generators import REGISTRY
from app.generators.service import fetch_items
from app.llm.errors import LLMError
from app.models import Attempt, Item, Response, SectionAttempt
from app.runtime import get_llm, get_stt, get_tts, run_background
from app.schemas import (
    AttemptOut,
    CreateAttempt,
    ResultsOut,
    ReviewItem,
    RunItem,
    RunOut,
    SectionResult,
    SectionStatus,
    TaskInfo,
    TaskResult,
)
from app.scoring.bands import adaptive_band, estimate_band
from app.scoring.dispatch import score_response
from app.spec import Difficulty, Section, TaskType

log = logging.getLogger(__name__)

GRACE = timedelta(seconds=3)  # network slack when a client submits right at the deadline
IMPLEMENTED_SECTIONS = frozenset({Section.READING, Section.LISTENING, Section.WRITING, Section.SPEAKING})
MAX_PARALLEL_GENERATION = 3  # each LLM call is a separate `claude -p` process; keep RAM use modest on an 8 GB laptop
AUDIO_REFETCH_WINDOW = timedelta(seconds=8)  # lets a dropped/duplicated request retry without granting a replay
DISCLAIMER = "These are estimated scores for practice only. They are not official ETS scores."


class ExamError(Exception):
    """Raised for invalid requests; the router maps `status` to an HTTP code."""

    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


def _now() -> datetime:
    return datetime.now(UTC)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


# ---------- create + generate ----------


def _task_entry(task_type: TaskType, count: int, seconds: int) -> dict[str, Any]:
    return {"task_type": task_type.value, "budget_seconds": seconds, "count": count, "deadline": None}


def _initial_meta(section: Section, mode: str, level: Difficulty, task_types: list[TaskType]) -> dict[str, Any]:
    base: dict[str, Any] = {"current": 0, "warnings": [], "stages_done": [], "level": level.value}
    if mode in ("full", "section") and section in spec.ADAPTIVE_STAGES:  # Reading / Listening sections are two-stage adaptive
        stages = spec.ADAPTIVE_STAGES[section]
        levels = spec.route_levels(level)
        return {**base, "adaptive": True, "stage": spec.ROUTER, "route": None,
                "tasks": [_task_entry(*x) for x in stages[spec.ROUTER]],
                "candidates": {k: {"level": levels[k].value, "tasks": [_task_entry(*x) for x in stages[k]]} for k in (spec.LOWER, spec.UPPER)}}
    return {**base, "adaptive": False, "stage": spec.MAIN,
            "tasks": [_task_entry(t, spec.TASK_ITEM_COUNT[t], spec.TASK_SECONDS[t]) for t in task_types]}


def create_attempt(db: Session, req: CreateAttempt) -> Attempt:
    if req.mode == "full":
        sections = list(spec.SECTION_ORDER)
        task_types: dict[Section, list[TaskType]] = {s: list(spec.SECTION_TASKS[s]) for s in sections}
    elif req.mode == "weak":
        wanted = set(req.task_types or [])
        if not wanted:
            raise ExamError("task_types is required for a weak-spot session")
        sections = [s for s in spec.SECTION_ORDER if wanted & set(spec.SECTION_TASKS[s])]
        task_types = {s: [t for t in spec.SECTION_TASKS[s] if t in wanted] for s in sections}  # official task order
    elif req.mode == "task":
        if req.task_type is None:
            raise ExamError("task_type is required for single-task mode")
        sections = [spec.TASK_SECTION[req.task_type]]
        task_types = {sections[0]: [req.task_type]}
    else:
        if req.section is None:
            raise ExamError("section is required for single-section mode")
        sections = [req.section]
        task_types = {req.section: list(spec.SECTION_TASKS[req.section])}
    level = req.difficulty
    timed = True if req.exam_mode == "exam" else req.timed
    attempt = Attempt(mode=req.mode, difficulty=level.value, exam_mode=req.exam_mode, timed=timed)
    for section in sections:
        attempt.sections.append(SectionAttempt(section=section.value, status="generating", gen={},
                                               meta=_initial_meta(section, req.mode, level, task_types[section])))
    db.add(attempt)
    db.commit()
    run_background(generate_pipeline, attempt.id)
    return attempt


def _fetch_task(task_type: TaskType, difficulty: Difficulty, count: int) -> tuple[list[Item], list[str]]:
    with SessionLocal() as db:  # one session per thread
        return fetch_items(db, get_llm(), task_type, difficulty, count)


def _build_audio(db: Session, item_ids: list[int]) -> None:
    """Assign voices, then synthesize audio for items with clips (grouped by voice so each model loads once)."""
    tts = get_tts()
    jobs: list[tuple[list[dict[str, Any]], float]] = []
    for item_id in item_ids:
        item = db.get(Item, item_id)
        if item is None or not audio_parts(item.payload):
            continue
        payload = copy.deepcopy(item.payload)
        parts = audio_parts(payload)
        if any("audio_key" not in part for part in parts):  # seeds reused from an earlier exam already have voices and keys
            assign_script_voices([line for part in parts for line in part["script"]], tts.available_voices())
            for part in parts:
                part["audio_key"] = script_key(part["script"], part["length_scale"])
            item.payload = payload
        jobs += [(part["script"], part["length_scale"]) for part in parts]
    db.commit()
    if jobs:
        AudioBuilder(tts, settings.audio_dir).build_many(jobs)


def _generate_stage(db: Session, sa: SectionAttempt, stage: str, level: Difficulty, tasks: list[dict[str, Any]]) -> list[str]:
    """Obtain unique items for every task of one stage (tasks in parallel) and bind them as that stage's Responses."""
    with ThreadPoolExecutor(max_workers=min(len(tasks), MAX_PARALLEL_GENERATION)) as pool:
        futures = [pool.submit(_fetch_task, TaskType(t["task_type"]), level, t["count"]) for t in tasks]
        results = [f.result() for f in futures]
    _build_audio(db, [item.id for items, _ in results for item in items])
    warnings: list[str] = []
    position = 0
    for (items, task_warnings), task in zip(results, tasks, strict=True):  # task order = exam order
        warnings.extend(task_warnings)
        gen = REGISTRY[TaskType(task["task_type"])]
        if items and gen.order_key(items[0].payload) is not None:
            items = sorted(items, key=lambda it: gen.order_key(it.payload) or 0)
        for item in items:
            db.add(Response(section_attempt_id=sa.id, item_id=item.id, position=position, stage=stage))
            position += 1
    db.commit()
    return warnings


def generate_pipeline(attempt_id: int) -> None:
    """Background job: generate the attempt's sections in exam order, so later sections prepare while the user works."""
    with SessionLocal() as db:
        order = [Section(sa.section) for sa in get_attempt(db, attempt_id).sections]
    for section in sorted(order, key=spec.SECTION_ORDER.index):
        generate_section(attempt_id, section.value)


def generate_section(attempt_id: int, section: str) -> None:
    """Generate a section's first stage (the section becomes 'ready'), then both candidate second modules."""
    with SessionLocal() as db:
        sa = _section(db, attempt_id, section)
        attempt = get_attempt(db, attempt_id)
        meta = copy.deepcopy(sa.meta)
        try:
            warnings = _generate_stage(db, sa, meta["stage"], Difficulty(meta["level"]), meta["tasks"])
        except Exception as exc:
            log.exception("generation failed")
            sa.status = "failed"
            meta["error"] = str(exc)
            sa.meta = meta
            db.commit()
            return
        meta["warnings"].extend(warnings)
        sa.meta = meta
        sa.status = "ready"
        db.commit()
        if not meta.get("adaptive"):
            return
        # Both possible second modules are prepared while the user takes the router; the unused one returns to the item bank.
        gen = {"candidate_warnings": [], "candidate_errors": {}}
        for kind in (spec.LOWER, spec.UPPER):
            cand = meta["candidates"][kind]
            try:
                gen["candidate_warnings"] += _generate_stage(db, sa, kind, Difficulty(cand["level"]), cand["tasks"])
            except Exception as exc:
                log.exception("candidate module generation failed")
                db.rollback()
                gen["candidate_errors"][kind] = str(exc)
        gen["candidates_ready"] = True
        sa.gen = gen  # the generation job owns this column; requests never write it
        db.commit()
        _try_route(db, attempt, sa)


# ---------- lookups ----------


def _section(db: Session, attempt_id: int, section: str) -> SectionAttempt:
    sa = db.scalar(select(SectionAttempt).where(SectionAttempt.attempt_id == attempt_id, SectionAttempt.section == section))
    if sa is None:
        raise ExamError("Section not found in this attempt", 404)
    return sa


def get_attempt(db: Session, attempt_id: int) -> Attempt:
    attempt = db.get(Attempt, attempt_id)
    if attempt is None:
        raise ExamError("Attempt not found", 404)
    return attempt


def _tasks(sa: SectionAttempt) -> list[dict[str, Any]]:
    return sa.meta["tasks"]


def _task_infos(sa: SectionAttempt) -> list[TaskInfo]:
    return [TaskInfo(task_type=TaskType(t["task_type"]), budget_seconds=t["budget_seconds"], count=t["count"]) for t in _tasks(sa)]


def _stage_info(sa: SectionAttempt) -> tuple[str, str, int]:
    """(stage name, label, stage count) for the status views."""
    meta = sa.meta
    count = 2 if meta.get("adaptive") else 1
    stage = meta.get("stage", spec.MAIN)
    label = "" if count == 1 else ("Module 1" if stage == spec.ROUTER else "Module 2")
    return stage, label, count


def _in_current_task(sa: SectionAttempt, resp: Response, item: Item) -> bool:
    return resp.stage == sa.meta["stage"] and _tasks(sa)[sa.meta["current"]]["task_type"] == item.task_type


# ---------- timers ----------


def _set_meta(sa: SectionAttempt, meta: dict[str, Any]) -> None:
    sa.meta = copy.deepcopy(meta)


def _stage_record(meta: dict[str, Any]) -> dict[str, Any]:
    tasks = [{k: v for k, v in t.items() if k != "deadline"} for t in meta["tasks"]]
    return {"name": meta["stage"], "level": meta["level"], "tasks": tasks}


def _finish(db: Session, attempt: Attempt, sa: SectionAttempt) -> None:
    meta = copy.deepcopy(sa.meta)
    meta["stages_done"].append(_stage_record(meta))
    meta["current"] = len(meta["tasks"])
    _set_meta(sa, meta)
    sa.status = "scoring"
    db.commit()
    run_background(score_section, attempt.id, sa.section)


def _score_stage(db: Session, attempt: Attempt, sa: SectionAttempt, stage: str) -> tuple[float, float]:
    """Machine-score one stage's responses now (used for routing); returns (points, max points)."""
    rows = db.execute(select(Response, Item).join(Item, Item.id == Response.item_id)
                      .where(Response.section_attempt_id == sa.id, Response.stage == stage)).all()
    for resp, item in rows:
        if resp.score is None:
            resp.score, resp.max_score, resp.feedback = score_response(
                get_llm(), TaskType(item.task_type), item.payload, resp.answer, Difficulty(attempt.difficulty))
    db.commit()
    return sum(r.score or 0 for r, _ in rows), sum(r.max_score or 0 for r, _ in rows)


def _route(db: Session, attempt: Attempt, sa: SectionAttempt, meta: dict[str, Any], anchor: datetime) -> None:
    """The router is done: score it, pick the lower or upper module, and enter it as soon as it is available."""
    meta["stages_done"].append(_stage_record(meta))
    _set_meta(sa, meta)
    points, maximum = _score_stage(db, attempt, sa, spec.ROUTER)
    fraction = points / maximum if maximum else 0.0
    choice = spec.UPPER if fraction >= spec.ROUTE_UP_THRESHOLD else spec.LOWER
    meta["route"] = {"to": choice, "router_fraction": round(fraction, 3), "router_level": meta["level"],
                     "module_level": meta["candidates"][choice]["level"]}
    meta["stage"] = "pending"
    _set_meta(sa, meta)
    sa.status = "preparing_next"
    db.commit()
    db.refresh(sa)
    if (sa.gen or {}).get("candidates_ready"):
        _enter_module(db, attempt, sa, anchor)


def _try_route(db: Session, attempt: Attempt, sa: SectionAttempt) -> None:
    """Called by the generation job when the candidate modules are ready, in case the user is already waiting."""
    db.refresh(sa)
    if sa.status == "preparing_next":
        _enter_module(db, attempt, sa, _now())


def _enter_module(db: Session, attempt: Attempt, sa: SectionAttempt, anchor: datetime) -> None:
    if sa.status != "preparing_next":
        return  # already entered (the user's request and the generation job can both arrive here)
    meta = copy.deepcopy(sa.meta)
    choice = meta["route"]["to"]
    counts = {k: db.query(Response).filter(Response.section_attempt_id == sa.id, Response.stage == k).count() for k in (spec.LOWER, spec.UPPER)}
    if counts[choice] == 0:  # that module could not be generated: fall back to the other one
        other = spec.LOWER if choice == spec.UPPER else spec.UPPER
        if counts[other] == 0:
            sa.status = "failed"
            meta["error"] = "The second module could not be prepared."
            _set_meta(sa, meta)
            db.commit()
            return
        choice = other
        meta["route"].update({"to": choice, "module_level": meta["candidates"][choice]["level"], "fallback": True})
    unused = spec.LOWER if choice == spec.UPPER else spec.UPPER
    stale = db.execute(select(Response, Item).join(Item, Item.id == Response.item_id)
                       .where(Response.section_attempt_id == sa.id, Response.stage == unused)).all()
    for resp, item in stale:  # unused module: its generated items go back to the bank for a later exam
        if item.source == "generated":
            item.served = False
        db.delete(resp)
    cand = meta["candidates"][choice]
    meta.update({"stage": choice, "level": cand["level"], "tasks": copy.deepcopy(cand["tasks"]), "current": 0})
    if attempt.timed:
        meta["tasks"][0]["deadline"] = _iso(anchor + timedelta(seconds=meta["tasks"][0]["budget_seconds"]))
    _set_meta(sa, meta)
    sa.status = "in_progress"
    db.commit()


def _advance(db: Session, attempt: Attempt, sa: SectionAttempt, anchor: datetime) -> None:
    """Move to the next task; its clock starts at `anchor` (now, or the previous deadline if we lapsed)."""
    meta = copy.deepcopy(sa.meta)
    meta["current"] += 1
    if meta["current"] >= len(meta["tasks"]):
        if meta.get("adaptive") and meta["stage"] == spec.ROUTER:
            _route(db, attempt, sa, meta, anchor)
        else:
            _finish(db, attempt, sa)
        return
    if attempt.timed:
        task = meta["tasks"][meta["current"]]
        task["deadline"] = _iso(anchor + timedelta(seconds=task["budget_seconds"]))
    _set_meta(sa, meta)
    db.commit()


def sync_section(db: Session, attempt: Attempt, sa: SectionAttempt) -> None:
    """Server-side enforcement: auto-advance (and finally auto-submit) tasks whose deadline has passed."""
    while sa.status == "in_progress" and attempt.timed:
        task = _tasks(sa)[sa.meta["current"]]
        deadline = _parse(task["deadline"])
        if _now() <= deadline + GRACE:
            return
        _advance(db, attempt, sa, anchor=deadline)


# ---------- run ----------


def start_section(db: Session, attempt_id: int, section: str) -> None:
    attempt = get_attempt(db, attempt_id)
    sa = _section(db, attempt_id, section)
    if sa.status == "in_progress":
        return
    if sa.status != "ready":
        raise ExamError(f"Section is {sa.status}; it cannot be started", 409)
    order = spec.SECTION_ORDER.index
    if any(order(Section(o.section)) < order(Section(sa.section)) and o.status not in ("scoring", "scored", "scoring_failed")
           for o in attempt.sections):
        raise ExamError("Finish the previous section first", 409)
    meta = copy.deepcopy(sa.meta)
    if attempt.timed:
        first = meta["tasks"][0]
        first["deadline"] = _iso(_now() + timedelta(seconds=first["budget_seconds"]))
    _set_meta(sa, meta)
    sa.status = "in_progress"
    sa.started_at = _now()
    db.commit()


def get_run(db: Session, attempt_id: int, section: str) -> RunOut:
    attempt = get_attempt(db, attempt_id)
    sa = _section(db, attempt_id, section)
    sync_section(db, attempt, sa)
    db.refresh(sa)
    tasks = _task_infos(sa)
    stage, label, stage_count = _stage_info(sa)
    base = {"status": sa.status, "server_now": _iso(_now()), "tasks": tasks, "stage": stage, "stage_label": label, "stage_count": stage_count}
    if sa.status != "in_progress":
        return RunOut(current_task=sa.meta["current"], task_type=None, task_deadline=None, items=[], **base)
    current = sa.meta["current"]
    task_type = tasks[current].task_type
    rows = db.execute(
        select(Response, Item).join(Item, Item.id == Response.item_id)
        .where(Response.section_attempt_id == sa.id, Response.stage == sa.meta["stage"], Item.task_type == task_type.value)
        .order_by(Response.position)
    ).all()
    exam = attempt.exam_mode == "exam"
    items = [RunItem(response_id=r.id, position=r.position, task_type=task_type, prompt=REGISTRY[task_type].public_prompt(i.payload),
                     answer=r.answer, has_audio=bool(audio_parts(i.payload)), audio_parts=len(audio_parts(i.payload)),
                     audio_played=[exam and bool(((r.meta or {}).get("audio") or {}).get(str(k), {}).get("plays"))
                                   for k in range(len(audio_parts(i.payload)))]) for r, i in rows]
    return RunOut(current_task=current, task_type=task_type, task_deadline=_tasks(sa)[current]["deadline"], items=items, **base)


def save_response(db: Session, attempt_id: int, response_id: int, answer: dict[str, Any]) -> None:
    attempt = get_attempt(db, attempt_id)
    resp = db.get(Response, response_id)
    sa = db.get(SectionAttempt, resp.section_attempt_id) if resp else None
    if resp is None or sa is None or sa.attempt_id != attempt_id:
        raise ExamError("Response not found", 404)
    sync_section(db, attempt, sa)
    if sa.status != "in_progress":
        raise ExamError("Time is up or the section is closed; answers are locked", 409)
    item = db.get(Item, resp.item_id)
    assert item is not None
    if not _in_current_task(sa, resp, item):
        raise ExamError("That task is closed; answers are locked", 409)
    try:
        resp.answer = REGISTRY[TaskType(item.task_type)].clean_answer(answer)
    except ValueError as exc:
        raise ExamError(str(exc)) from exc
    db.commit()


def get_audio(db: Session, attempt_id: int, response_id: int, part: int = 0) -> Path:
    """Path of an item's audio clip. Exam mode: one play per clip (a short re-fetch window tolerates retries)."""
    attempt = get_attempt(db, attempt_id)
    resp = db.get(Response, response_id)
    sa = db.get(SectionAttempt, resp.section_attempt_id) if resp else None
    if resp is None or sa is None or sa.attempt_id != attempt_id:
        raise ExamError("Response not found", 404)
    item = db.get(Item, resp.item_id)
    parts = audio_parts(item.payload) if item else []
    key = parts[part].get("audio_key") if 0 <= part < len(parts) else None
    path = AudioBuilder(get_tts(), settings.audio_dir).path_for(key) if key else None
    if path is None or not path.exists():
        raise ExamError("No audio for this item", 404)
    sync_section(db, attempt, sa)
    if sa.status in ("generating", "ready", "failed", "preparing_next"):
        raise ExamError("The section has not started", 409)
    if sa.status == "in_progress":
        if not _in_current_task(sa, resp, item):
            raise ExamError("That task is closed", 409)
        if attempt.exam_mode == "exam":
            meta = copy.deepcopy(resp.meta or {})
            plays = meta.setdefault("audio", {}).setdefault(str(part), {})
            first = plays.get("first_play_at")
            if first and _now() - _parse(first) > AUDIO_REFETCH_WINDOW:
                raise ExamError("Audio plays only once in exam mode", 403)
            plays.setdefault("first_play_at", _iso(_now()))
            plays["plays"] = plays.get("plays", 0) + 1
            resp.meta = meta
            db.commit()
    return path  # after the section ends, audio is open for review


MAX_RECORDING_BYTES = 10 * 1024 * 1024
MIN_RECORDING_BYTES = 100
RECORDING_GRACE_SECONDS = 5  # recorder start/stop latency on top of the response window
_EXTENSIONS = {"audio/webm": "webm", "audio/ogg": "ogg", "audio/mp4": "m4a", "audio/mpeg": "mp3", "audio/wav": "wav",
               "audio/x-wav": "wav", "audio/wave": "wav"}


def _speaking_context(db: Session, attempt_id: int, response_id: int, part: int) -> tuple[Attempt, Response, SectionAttempt, Item]:
    attempt = get_attempt(db, attempt_id)
    resp = db.get(Response, response_id)
    sa = db.get(SectionAttempt, resp.section_attempt_id) if resp else None
    item = db.get(Item, resp.item_id) if resp else None
    if resp is None or sa is None or sa.attempt_id != attempt_id or item is None:
        raise ExamError("Response not found", 404)
    if TaskType(item.task_type) not in SPEAKING_TASKS:
        raise ExamError("This item does not take recordings", 400)
    if not 0 <= part < len(audio_parts(item.payload)):
        raise ExamError("No such part", 404)
    return attempt, resp, sa, item


def save_recording(db: Session, attempt_id: int, response_id: int, part: int, data: bytes, content_type: str,
                   duration_ms: int) -> None:
    attempt, resp, sa, item = _speaking_context(db, attempt_id, response_id, part)
    sync_section(db, attempt, sa)
    if sa.status != "in_progress":
        raise ExamError("Time is up or the section is closed; recordings are locked", 409)
    if not _in_current_task(sa, resp, item):
        raise ExamError("That task is closed; recordings are locked", 409)
    ext = _EXTENSIONS.get(content_type.split(";")[0].strip().lower())
    if ext is None:
        raise ExamError(f"Unsupported audio type '{content_type}'", 415)
    if not MIN_RECORDING_BYTES <= len(data) <= MAX_RECORDING_BYTES:
        raise ExamError("Recording is empty or too large", 400)
    limit_ms = (item.payload["response_seconds"] + RECORDING_GRACE_SECONDS) * 1000
    if duration_ms > limit_ms:
        raise ExamError("Recording is longer than the response time allows", 400)
    answer = copy.deepcopy(resp.answer or {"parts": {}})
    if attempt.exam_mode == "exam" and str(part) in answer["parts"]:
        raise ExamError("This response was already recorded; exam mode allows one attempt", 409)
    rel = f"{attempt_id}/{response_id}_{part}.{ext}"
    path = settings.recordings_dir / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    answer["parts"][str(part)] = {"file": rel, "duration_ms": duration_ms, "content_type": content_type.split(";")[0].strip()}
    resp.answer = answer
    db.commit()


def get_recording(db: Session, attempt_id: int, response_id: int, part: int) -> tuple[Path, str]:
    attempt, resp, sa, _ = _speaking_context(db, attempt_id, response_id, part)
    sync_section(db, attempt, sa)
    if sa.status == "in_progress" and attempt.exam_mode == "exam":
        raise ExamError("Recordings can be played back after the section ends", 403)
    info = ((resp.answer or {}).get("parts") or {}).get(str(part))
    path = settings.recordings_dir / info["file"] if info else None
    if path is None or not path.exists():
        raise ExamError("No recording", 404)
    return path, info["content_type"]


def advance(db: Session, attempt_id: int, section: str) -> None:
    attempt = get_attempt(db, attempt_id)
    sa = _section(db, attempt_id, section)
    sync_section(db, attempt, sa)
    if sa.status == "in_progress":
        _advance(db, attempt, sa, anchor=_now())


def submit(db: Session, attempt_id: int, section: str) -> None:
    attempt = get_attempt(db, attempt_id)
    sa = _section(db, attempt_id, section)
    sync_section(db, attempt, sa)
    if sa.status == "in_progress":
        _finish(db, attempt, sa)


# ---------- scoring ----------


def _section_band(sa: SectionAttempt, rows: list[Any], difficulty: Difficulty) -> float:
    """Adaptive sections combine their stages (each mapped to a band interval by its role); others use one stage."""
    meta = sa.meta
    if meta.get("adaptive") and meta.get("route"):
        stages = []
        for rec in meta["stages_done"]:
            in_stage = [r for r, _ in rows if r.stage == rec["name"]]
            stages.append((rec["name"], Difficulty(rec["level"]), sum(r.score or 0 for r in in_stage), sum(r.max_score or 0 for r in in_stage)))
        return adaptive_band(stages)
    points = sum(r.score or 0 for r, _ in rows)
    max_points = sum(r.max_score or 0 for r, _ in rows)
    return estimate_band(points, max_points, Difficulty(meta.get("level", difficulty.value)))


SPEAKING_TASKS = frozenset({TaskType.LISTEN_AND_REPEAT, TaskType.TAKE_INTERVIEW})


def score_section(attempt_id: int, section: str) -> None:
    """Background job: score every response, then derive the section band."""
    stt = None
    try:
        with SessionLocal() as db:
            attempt = get_attempt(db, attempt_id)
            sa = _section(db, attempt_id, section)
            difficulty = Difficulty(attempt.difficulty)
            llm = get_llm()
            failures = 0
            rows = db.execute(
                select(Response, Item).join(Item, Item.id == Response.item_id).where(Response.section_attempt_id == sa.id)
            ).all()
            if any(TaskType(i.task_type) in SPEAKING_TASKS for _, i in rows):
                stt = get_stt()
            for resp, item in rows:
                if resp.score is not None:
                    continue  # already scored (retry path)
                task_type = TaskType(item.task_type)
                try:
                    score, max_score, feedback = score_response(llm, task_type, item.payload, resp.answer, difficulty, stt)
                except (LLMError, SttError) as exc:
                    failures += 1
                    resp.feedback = {"error": str(exc)}
                    db.commit()
                    continue
                resp.transcript = feedback.pop("_transcript", None)
                resp.score, resp.max_score, resp.feedback = score, max_score, feedback
                db.commit()
            if failures:
                sa.status = "scoring_failed"
                db.commit()
                return
            sa.band = _section_band(sa, rows, difficulty)
            sa.status = "scored"
            if all(s.status == "scored" for s in attempt.sections):
                attempt.status = "complete"
                attempt.finished_at = _now()
                if attempt.mode == "full":
                    attempt.overall_band = spec.overall_band([s.band for s in attempt.sections if s.band is not None])
            db.commit()
    finally:
        if stt is not None:
            stt.close()  # free the Whisper model; the next scoring job reloads it in ~0.3 s


def rescore(db: Session, attempt_id: int, section: str) -> None:
    sa = _section(db, attempt_id, section)
    if sa.status != "scoring_failed":
        raise ExamError("Nothing to rescore", 409)
    sa.status = "scoring"
    db.commit()
    run_background(score_section, attempt_id, section)


# ---------- views ----------


def attempt_out(db: Session, attempt: Attempt) -> AttemptOut:
    for sa in attempt.sections:
        sync_section(db, attempt, sa)
    db.expire_all()  # background jobs commit from other sessions
    sections = []
    for sa in attempt.sections:
        current = sa.meta["current"]
        deadline = _tasks(sa)[current]["deadline"] if sa.status == "in_progress" else None
        stage, label, stage_count = _stage_info(sa)
        sections.append(SectionStatus(
            section=Section(sa.section), status=sa.status, band=sa.band, stage=stage, stage_label=label, stage_count=stage_count,
            route=sa.meta.get("route"), tasks=_task_infos(sa), current_task=current, task_deadline=deadline,
            warnings=sa.meta.get("warnings", []) + (sa.gen or {}).get("candidate_warnings", []), error=sa.meta.get("error"),
        ))
    return AttemptOut(id=attempt.id, mode=attempt.mode, difficulty=Difficulty(attempt.difficulty), exam_mode=attempt.exam_mode,
                      timed=attempt.timed, status=attempt.status, server_now=_iso(_now()), sections=sections)


def build_results(db: Session, attempt: Attempt) -> ResultsOut:
    db.expire_all()
    out_sections: list[SectionResult] = []
    for sa in attempt.sections:
        rows = db.execute(
            select(Response, Item).join(Item, Item.id == Response.item_id)
            .where(Response.section_attempt_id == sa.id).order_by(Response.position)
        ).all()
        tasks: list[TaskResult] = []
        stages = sa.meta["stages_done"] or [{"name": sa.meta["stage"], "level": sa.meta["level"], "tasks": _tasks(sa)}]
        for rec in stages:
            label = "" if not sa.meta.get("adaptive") else ("Module 1" if rec["name"] == spec.ROUTER else "Module 2")
            for t in rec["tasks"]:
                task_rows = [(r, i) for r, i in rows if i.task_type == t["task_type"] and r.stage == rec["name"]]
                tasks.append(TaskResult(
                    stage=rec["name"], stage_label=label, level=Difficulty(rec["level"]), task_type=TaskType(t["task_type"]),
                    points=sum(r.score or 0 for r, _ in task_rows),
                    max_points=sum(r.max_score or 0 for r, _ in task_rows),
                    items=[ReviewItem(response_id=r.id, task_type=TaskType(i.task_type), position=r.position, prompt=i.payload,
                                      answer=r.answer, score=r.score, max_score=r.max_score, feedback=r.feedback)
                           for r, i in task_rows],
                ))
        scored = sa.status == "scored"
        out_sections.append(SectionResult(
            section=Section(sa.section), status=sa.status, band=sa.band,
            points=sum(t.points for t in tasks) if scored else None,
            max_points=sum(t.max_points for t in tasks) if scored else None,
            tasks=tasks, error=sa.meta.get("error"), route=sa.meta.get("route"),
        ))
    bands = [s.band for s in out_sections if s.band is not None]
    overall = spec.overall_band(bands) if attempt.mode == "full" and len(bands) == len(spec.SECTION_ORDER) else None
    return ResultsOut(attempt_id=attempt.id, difficulty=Difficulty(attempt.difficulty), mode=attempt.mode, status=attempt.status,
                      overall_band=overall, disclaimer=DISCLAIMER, sections=out_sections)
