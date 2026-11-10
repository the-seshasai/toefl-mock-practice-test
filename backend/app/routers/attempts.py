from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas import AttemptOut, CreateAttempt, ResultsOut, RunOut, SaveAnswer
from app.services import exam
from app.spec import Section

Db = Annotated[Session, Depends(get_session)]

router = APIRouter(prefix="/api/attempts", tags=["attempts"])


def _fail(exc: exam.ExamError) -> NoReturn:
    raise HTTPException(status_code=exc.status, detail=str(exc)) from exc


@router.post("", response_model=AttemptOut)
def create(req: CreateAttempt, db: Db) -> AttemptOut:
    try:
        return exam.attempt_out(db, exam.create_attempt(db, req))
    except exam.ExamError as exc:
        _fail(exc)


@router.get("/{attempt_id}", response_model=AttemptOut)
def read(attempt_id: int, db: Db) -> AttemptOut:
    try:
        return exam.attempt_out(db, exam.get_attempt(db, attempt_id))
    except exam.ExamError as exc:
        _fail(exc)


@router.post("/{attempt_id}/sections/{section}/start", response_model=AttemptOut)
def start(attempt_id: int, section: Section, db: Db) -> AttemptOut:
    try:
        exam.start_section(db, attempt_id, section.value)
        return exam.attempt_out(db, exam.get_attempt(db, attempt_id))
    except exam.ExamError as exc:
        _fail(exc)


@router.get("/{attempt_id}/sections/{section}/run", response_model=RunOut)
def run(attempt_id: int, section: Section, db: Db) -> RunOut:
    try:
        return exam.get_run(db, attempt_id, section.value)
    except exam.ExamError as exc:
        _fail(exc)


@router.put("/{attempt_id}/responses/{response_id}", status_code=204)
def save(attempt_id: int, response_id: int, body: SaveAnswer, db: Db) -> None:
    try:
        exam.save_response(db, attempt_id, response_id, body.answer)
    except exam.ExamError as exc:
        _fail(exc)


@router.get("/{attempt_id}/responses/{response_id}/audio")
def audio(attempt_id: int, response_id: int, db: Db, part: int = 0) -> FileResponse:
    try:
        path = exam.get_audio(db, attempt_id, response_id, part)
    except exam.ExamError as exc:
        _fail(exc)
    return FileResponse(path, media_type="audio/wav", headers={"Cache-Control": "no-store"})


@router.post("/{attempt_id}/responses/{response_id}/recording", status_code=204)
async def upload_recording(attempt_id: int, response_id: int, request: Request, db: Db, part: int = 0, duration_ms: int = 0) -> None:
    if int(request.headers.get("content-length") or 0) > exam.MAX_RECORDING_BYTES:
        raise HTTPException(status_code=413, detail="Recording too large")
    data = await request.body()
    try:
        exam.save_recording(db, attempt_id, response_id, part, data, request.headers.get("content-type", ""), duration_ms)
    except exam.ExamError as exc:
        _fail(exc)


@router.get("/{attempt_id}/responses/{response_id}/recording")
def recording(attempt_id: int, response_id: int, db: Db, part: int = 0) -> FileResponse:
    try:
        path, media_type = exam.get_recording(db, attempt_id, response_id, part)
    except exam.ExamError as exc:
        _fail(exc)
    return FileResponse(path, media_type=media_type, headers={"Cache-Control": "no-store"})


@router.post("/{attempt_id}/sections/{section}/advance", response_model=RunOut)
def advance(attempt_id: int, section: Section, db: Db) -> RunOut:
    try:
        exam.advance(db, attempt_id, section.value)
        return exam.get_run(db, attempt_id, section.value)
    except exam.ExamError as exc:
        _fail(exc)


@router.post("/{attempt_id}/sections/{section}/submit", response_model=RunOut)
def submit(attempt_id: int, section: Section, db: Db) -> RunOut:
    try:
        exam.submit(db, attempt_id, section.value)
        return exam.get_run(db, attempt_id, section.value)
    except exam.ExamError as exc:
        _fail(exc)


@router.post("/{attempt_id}/sections/{section}/rescore", response_model=AttemptOut)
def rescore(attempt_id: int, section: Section, db: Db) -> AttemptOut:
    try:
        exam.rescore(db, attempt_id, section.value)
        return exam.attempt_out(db, exam.get_attempt(db, attempt_id))
    except exam.ExamError as exc:
        _fail(exc)


@router.get("/{attempt_id}/results", response_model=ResultsOut)
def results(attempt_id: int, db: Db) -> ResultsOut:
    try:
        return exam.build_results(db, exam.get_attempt(db, attempt_id))
    except exam.ExamError as exc:
        _fail(exc)
