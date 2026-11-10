import os
import tempfile

# Must run before app modules are imported so tests never touch the real data/ directory.
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="toefl-test-")

import pytest


@pytest.fixture(autouse=True)
def fresh_db():
    from app.db import Base, engine, init_db

    Base.metadata.drop_all(engine)
    init_db()
    yield


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch):
    from app.services import exam
    from tests.flow import Clock

    c = Clock()
    monkeypatch.setattr(exam, "_now", c.now)
    return c


@pytest.fixture
def llm():
    from app import runtime
    from tests.helpers import FakeStt, FakeTTS, RoutingFake

    fake = RoutingFake(score=4.0)
    runtime.set_llm_factory(lambda: fake)
    runtime.set_background_runner(lambda fn, *a: fn(*a))  # run jobs inline, deterministically
    tts, stt = FakeTTS(), FakeStt()
    runtime.set_tts_factory(lambda: tts)
    runtime.set_stt_factory(lambda: stt)
    fake.tts, fake.stt = tts, stt
    yield fake
    runtime.set_llm_factory(None)
    runtime.set_background_runner(None)
    runtime.set_tts_factory(None)
    runtime.set_stt_factory(None)


@pytest.fixture
def client(llm):
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c
