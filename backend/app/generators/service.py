import itertools
import logging
import random

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.generators import REGISTRY
from app.llm import LLMProvider
from app.models import Item
from app.spec import Difficulty, TaskType

log = logging.getLogger(__name__)


class NotEnoughItems(Exception):
    pass


def _unserved(db: Session, task_type: TaskType, difficulty: Difficulty | None, source: str, limit: int) -> list[Item]:
    q = select(Item).where(Item.task_type == task_type.value, Item.served.is_(False), Item.source == source)
    if difficulty is not None:
        q = q.where(Item.difficulty == difficulty.value)
    return list(db.scalars(q.order_by(Item.id).limit(limit)))


def fetch_items(db: Session, llm: LLMProvider, task_type: TaskType, difficulty: Difficulty,
                count: int) -> tuple[list[Item], list[str]]:
    """Return `count` never-served items plus warnings. Order: leftover generated -> new generation -> seed bank."""
    warnings: list[str] = []
    items = _unserved(db, task_type, difficulty, "generated", count)
    if len(items) < count:
        created = REGISTRY[task_type].generate(db, llm, difficulty, count - len(items))
        items += created[: count - len(items)]
    if len(items) < count:
        missing = count - len(items)
        pool = _unserved(db, task_type, difficulty, "seed", 50) or _unserved(db, task_type, None, "seed", 50)
        fallback = random.sample(pool, min(missing, len(pool)))
        if len(fallback) < missing:  # seeds exhausted: reuse them (cycling if need be) rather than blocking the exam
            reuse = list(db.scalars(select(Item).where(Item.task_type == task_type.value, Item.source == "seed")))
            same_level = [x for x in reuse if x.difficulty == difficulty.value]
            reuse = same_level or reuse  # repeat seeds of the requested level rather than drifting to another level
            random.shuffle(reuse)
            if reuse:
                fallback += [x for x, _ in zip(itertools.cycle(reuse), range(missing - len(fallback)), strict=False)]
                warnings.append(f"{task_type.value}: fallback items were repeated")
        items += fallback
        warnings.append(f"{task_type.value}: {len(fallback)} item(s) came from the fallback bank")
    if len(items) < count:
        raise NotEnoughItems(f"Could not obtain {count} items for {task_type.value}")
    for it in items:
        it.served = True
    db.commit()
    return items, warnings
