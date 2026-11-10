from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_session
from app.models import Attempt
from app.schemas import HistoryAttempt, HistoryOut

Db = Annotated[Session, Depends(get_session)]

router = APIRouter(prefix="/api/history", tags=["history"])


def _task_types(attempt: Attempt) -> list[str]:
    seen: list[str] = []
    for sa in attempt.sections:
        recs = sa.meta.get("stages_done") or [{"tasks": sa.meta.get("tasks", [])}]
        seen += [t["task_type"] for rec in recs for t in rec["tasks"] if t["task_type"] not in seen]
    return seen


@router.get("", response_model=HistoryOut)
def history(db: Db, limit: int = 200) -> HistoryOut:
    rows = db.scalars(
        select(Attempt).options(selectinload(Attempt.sections)).order_by(Attempt.started_at.desc(), Attempt.id.desc()).limit(min(max(limit, 1), 500))
    ).all()
    out: list[HistoryAttempt] = []
    for a in rows:
        bands = {s.section: s.band for s in a.sections if s.status in ("scored", "scoring_failed") or s.band is not None}
        if not bands and a.status == "in_progress":
            continue  # abandoned before anything was scored
        out.append(
            HistoryAttempt(
                id=a.id,
                mode=a.mode,
                difficulty=a.difficulty,  # type: ignore[arg-type]
                exam_mode=a.exam_mode,
                status=a.status,
                started_at=a.started_at.isoformat(),
                overall_band=a.overall_band,
                bands=bands,
                tasks=_task_types(a) if a.mode in ("task", "weak") else [],
            )
        )
    return HistoryOut(attempts=out)
