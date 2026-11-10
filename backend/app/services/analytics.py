"""Progress analytics: which task types are weakest, how each section is trending, which errors recur."""
from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import spec
from app.models import Attempt, Item, Response, SectionAttempt
from app.schemas import AnalyticsOut, SectionSummary, TaskStat
from app.scoring.bands import stage_band
from app.spec import Difficulty, Section, TaskType

RECENCY_DECAY = 0.8  # each older attempt counts 80% as much as the one after it
TREND_WINDOW = 3
RECENT_ATTEMPTS_FOR_ERRORS = 10
DEFAULT_WEAK_COUNT = 3


def _attempt_bands(db: Session) -> dict[TaskType, list[tuple[int, float, float, float]]]:
    """Per task type: [(attempt_id, band, points, max_points)] for every scored attempt, newest attempt first.

    A band comes from the points earned in one (attempt, stage, level) group, mapped with the same level-aware
    intervals used for section bands, so 70% on Advanced items counts for more than 70% on Beginner items.
    """
    rows = db.execute(
        select(Response, Item, SectionAttempt)
        .join(Item, Item.id == Response.item_id)
        .join(SectionAttempt, SectionAttempt.id == Response.section_attempt_id)
        .where(SectionAttempt.status == "scored", Response.score.is_not(None), Response.max_score > 0)
    ).all()
    groups: dict[tuple[int, str, str, str], list[float]] = defaultdict(lambda: [0.0, 0.0])
    for resp, item, sa in rows:
        g = groups[(sa.attempt_id, item.task_type, resp.stage, item.difficulty)]
        g[0] += resp.score or 0
        g[1] += resp.max_score or 0
    per_attempt: dict[tuple[int, str], list[tuple[float, float, float]]] = defaultdict(list)
    for (attempt_id, task, stage, level), (points, maximum) in groups.items():
        per_attempt[(attempt_id, task)].append((stage_band(stage, Difficulty(level), points, maximum), points, maximum))
    out: dict[TaskType, list[tuple[int, float, float, float]]] = defaultdict(list)
    for (attempt_id, task), parts in per_attempt.items():
        weight = sum(m for _, _, m in parts)
        out[TaskType(task)].append((attempt_id, sum(b * m for b, _, m in parts) / weight,
                                    sum(p for _, p, _ in parts), weight))
    for rows in out.values():
        rows.sort(key=lambda r: r[0], reverse=True)
    return out


def _task_stats(per_task: dict[TaskType, list[tuple[int, float, float, float]]]) -> list[TaskStat]:
    stats = []
    for task, rows in per_task.items():
        weights = [RECENCY_DECAY**i for i in range(len(rows))]
        band = sum(w * r[1] for w, r in zip(weights, rows, strict=True)) / sum(weights)
        earlier = [r[1] for r in rows[1 : 1 + TREND_WINDOW]]
        points, maximum = sum(r[2] for r in rows), sum(r[3] for r in rows)
        stats.append(TaskStat(
            task_type=task, section=spec.TASK_SECTION[task], band=round(band, 2), last_band=round(rows[0][1], 2),
            accuracy=round(points / maximum, 3) if maximum else 0.0, attempts=len(rows),
            trend=round(rows[0][1] - sum(earlier) / len(earlier), 2) if earlier else None,
        ))
    return sorted(stats, key=lambda s: (s.band, s.accuracy, s.task_type.value))


def weakest_task_types(db: Session, count: int = DEFAULT_WEAK_COUNT) -> list[TaskType]:
    return [s.task_type for s in _task_stats(_attempt_bands(db))[:count]]


def _error_categories(db: Session) -> dict[str, int]:
    recent = db.scalars(select(Attempt.id).where(Attempt.status != "in_progress").order_by(Attempt.id.desc())
                        .limit(RECENT_ATTEMPTS_FOR_ERRORS)).all()
    counts: dict[str, int] = defaultdict(int)
    if not recent:
        return {}
    rows = db.execute(
        select(Response, Item, SectionAttempt).join(Item, Item.id == Response.item_id)
        .join(SectionAttempt, SectionAttempt.id == Response.section_attempt_id)
        .where(SectionAttempt.attempt_id.in_(recent), Response.feedback.is_not(None))
    ).all()
    for resp, item, _ in rows:
        fb: dict[str, Any] = resp.feedback or {}
        if item.task_type in (TaskType.WRITE_EMAIL.value, TaskType.WRITE_ACADEMIC_DISCUSSION.value):
            notes = fb.get("errors", [])
        elif item.task_type == TaskType.TAKE_INTERVIEW.value:
            notes = [n for entry in fb.get("items", []) for n in entry.get("errors", [])]
        else:
            continue
        for note in notes:
            counts[note.get("category", "other")] += 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))


def build_analytics(db: Session) -> AnalyticsOut:
    stats = _task_stats(_attempt_bands(db))
    sections: list[SectionSummary] = []
    for section in spec.SECTION_ORDER:
        bands = [b for b, in db.execute(
            select(SectionAttempt.band).join(Attempt, Attempt.id == SectionAttempt.attempt_id)
            .where(SectionAttempt.section == section.value, SectionAttempt.status == "scored", SectionAttempt.band.is_not(None),
                   Attempt.mode.in_(["full", "section"])).order_by(Attempt.id)  # whole-section attempts only
        )]
        if bands:
            sections.append(SectionSummary(section=Section(section), latest=bands[-1], best=max(bands),
                                           average=round(sum(bands) / len(bands), 2), count=len(bands)))
    latest = db.scalar(select(Attempt.difficulty).join(SectionAttempt, SectionAttempt.attempt_id == Attempt.id)
                       .where(SectionAttempt.status == "scored").order_by(Attempt.id.desc()).limit(1))
    attempts_scored = len(set(db.scalars(select(SectionAttempt.attempt_id).where(SectionAttempt.status == "scored"))))
    return AnalyticsOut(
        attempts_scored=attempts_scored, tasks=stats, weakest=[s.task_type for s in stats[:DEFAULT_WEAK_COUNT]],
        sections=sections, error_categories=_error_categories(db),
        suggested_difficulty=Difficulty(latest) if latest else None,
    )
