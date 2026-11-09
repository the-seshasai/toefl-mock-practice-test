from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import spec
from app.config import settings
from app.db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="TOEFL iBT Practice (2026 format)", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=[settings.frontend_origin], allow_methods=["*"], allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "sections": [s.value for s in spec.SECTION_ORDER],
    }
