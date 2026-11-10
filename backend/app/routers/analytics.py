from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas import AnalyticsOut, AttemptOut, CreateAttempt, WeakSpotRequest
from app.services import analytics, exam

Db = Annotated[Session, Depends(get_session)]

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/analytics", response_model=AnalyticsOut)
def read_analytics(db: Db) -> AnalyticsOut:
    return analytics.build_analytics(db)


@router.post("/practice/weak-spots", response_model=AttemptOut)
def practice_weak_spots(req: WeakSpotRequest, db: Db) -> AttemptOut:
    """Start a targeted session on the task types you are weakest at (level-adjusted, recency weighted)."""
    stats = analytics.build_analytics(db)
    focus = [s.task_type for s in stats.tasks[: req.count]]
    if not focus:
        raise HTTPException(status_code=400, detail="Finish at least one scored practice first, so there is something to analyze.")
    level = req.difficulty or stats.suggested_difficulty
    if level is None:
        raise HTTPException(status_code=400, detail="Choose a difficulty.")
    try:
        attempt = exam.create_attempt(db, CreateAttempt(mode="weak", difficulty=level, exam_mode=req.exam_mode,
                                                        timed=req.timed, task_types=focus))
        return exam.attempt_out(db, attempt)
    except exam.ExamError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc)) from exc
