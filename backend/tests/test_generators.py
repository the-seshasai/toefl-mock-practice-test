import pytest

from app.db import SessionLocal
from app.generators import REGISTRY
from app.generators.service import fetch_items
from app.llm.fake import FakeProvider
from app.models import Item
from app.spec import Difficulty, TaskType
from tests.helpers import RoutingFake, bas_item, discussion_item, email_item

B = Difficulty.BEGINNER


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


def test_build_sentence_generates_validates_and_shuffles(db) -> None:
    bad = {**bas_item(), "correct_order": ["too", "short."]}
    llm = FakeProvider([{"items": [bas_item(), bad, bas_item()]}])
    items = REGISTRY[TaskType.BUILD_A_SENTENCE].generate(db, llm, B, need=2)
    assert len(items) == 2
    for it in items:
        assert sorted(it.payload["chunks"]) == sorted(it.payload["correct_order"])
        assert it.payload["chunks"] != it.payload["correct_order"]
        assert it.served is False and it.source == "generated" and len(it.content_hash) == 64
    assert "avoid" not in llm.calls[0]["prompt"].lower() or "${" not in llm.calls[0]["prompt"]


def test_duplicates_are_rejected(db) -> None:
    same = bas_item(900)
    gen = REGISTRY[TaskType.BUILD_A_SENTENCE]
    assert len(gen.generate(db, FakeProvider([{"items": [same]}]), B, need=1, max_attempts=1)) == 1
    assert gen.generate(db, FakeProvider([{"items": [same]}]), B, need=1, max_attempts=1) == []


def test_generation_retries_until_enough(db) -> None:
    llm = FakeProvider([{"items": [{"bogus": 1}]}, {"items": [bas_item()]}])
    items = REGISTRY[TaskType.BUILD_A_SENTENCE].generate(db, llm, B, need=1)
    assert len(items) == 1 and len(llm.calls) == 2


def test_email_and_discussion_generation(db) -> None:
    e = REGISTRY[TaskType.WRITE_EMAIL].generate(db, FakeProvider([{"items": [email_item()]}]), B, need=1)
    d = REGISTRY[TaskType.WRITE_ACADEMIC_DISCUSSION].generate(db, FakeProvider([{"items": [discussion_item()]}]), B, need=1)
    assert len(e) == 1 and len(d) == 1


def test_fetch_items_marks_served_and_keeps_leftovers(db) -> None:
    llm = RoutingFake()
    items, warnings = fetch_items(db, llm, TaskType.BUILD_A_SENTENCE, B, 10)
    assert len(items) == 10 and warnings == [] and all(i.served for i in items)
    leftovers = db.query(Item).filter(Item.source == "generated", Item.served.is_(False)).count()
    assert leftovers == 2  # batch of need+2; spares stay in the bank
    calls_before = len(llm.prompts)
    again, _ = fetch_items(db, llm, TaskType.BUILD_A_SENTENCE, B, 10)
    assert {i.id for i in again}.isdisjoint({i.id for i in items})
    assert len(llm.prompts) > calls_before


def test_fetch_items_falls_back_to_seed_bank(db) -> None:
    items, warnings = fetch_items(db, RoutingFake(fail_generation=True), TaskType.WRITE_EMAIL, B, 1)
    assert len(items) == 1 and items[0].source == "seed"
    assert any("fallback bank" in w for w in warnings)


def test_seed_reuse_when_exhausted_never_blocks(db) -> None:
    llm = RoutingFake(fail_generation=True)
    for _ in range(5):  # only 10 BaS seeds exist; 10 per exam -> second exam must reuse
        items, _ = fetch_items(db, llm, TaskType.BUILD_A_SENTENCE, B, 10)
        assert len(items) == 10
