import random

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Item
from app.spec import TaskType

DOMAINS: tuple[str, ...] = (
    "biology and ecology", "history", "business and economics", "psychology", "environmental science",
    "technology and computing", "art and design", "campus life and housing", "health and nutrition",
    "astronomy and space", "sociology", "literature and writing", "engineering", "music and culture",
    "geography and travel", "study skills and education", "chemistry and materials", "public policy",
)

ROTATION_WINDOW = 24


def pick_domain(db: Session, task_type: TaskType) -> str:
    """Choose among the least-recently-used domains for this task type so topics rotate."""
    recent = db.scalars(
        select(Item.topic).where(Item.task_type == task_type.value).order_by(Item.id.desc()).limit(ROTATION_WINDOW)
    ).all()
    counts = {d: recent.count(d) for d in DOMAINS}
    lowest = min(counts.values())
    return random.choice([d for d, c in counts.items() if c == lowest])
