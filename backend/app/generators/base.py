import hashlib
import logging
import random
import re
from abc import ABC, abstractmethod
from pathlib import Path
from string import Template
from typing import Any

from pydantic import BaseModel, ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.generators.topics import pick_domain
from app.llm import LLMProvider
from app.llm.errors import LLMError
from app.models import Item
from app.schemas import RawBatch
from app.spec import Difficulty, TaskType

log = logging.getLogger(__name__)

PROMPT_DIR = Path(__file__).parent / "prompts"
SYSTEM_PROMPT = (
    "You are an expert item writer for an English proficiency test. Write original content only; "
    "never reproduce real exam or copyrighted material. Output JSON only."
)
AVOID_LIMIT = 12


def aim(rng: tuple[int, int]) -> tuple[str, str]:
    """Prompt range: the middle 60% of the allowed range, because LLMs miss word counts by 10-15%."""
    margin = round((rng[1] - rng[0]) * 0.2)
    return str(rng[0] + margin), str(rng[1] - margin)


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def content_hash(task_type: TaskType, key: str) -> str:
    return hashlib.sha256(f"{task_type.value}|{normalize(key)}".encode()).hexdigest()


class TaskGenerator(ABC):
    """One generator per task type: render prompt -> LLM -> per-item parse + validate -> dedupe -> store."""

    task_type: TaskType
    prompt_file: str
    item_model: type[BaseModel]
    max_batch: int = 1

    @abstractmethod
    def params(self, difficulty: Difficulty) -> Any: ...

    @abstractmethod
    def validate(self, item: Any, params: Any) -> list[str]: ...

    @abstractmethod
    def content_key(self, item: Any) -> str: ...

    @abstractmethod
    def to_payload(self, item: Any, difficulty: Difficulty = Difficulty.INTERMEDIATE) -> dict[str, Any]: ...

    @abstractmethod
    def prompt_vars(self, params: Any, count: int, avoid: list[str]) -> dict[str, str]: ...

    def order_key(self, payload: dict[str, Any]) -> float | None:
        """If set, items of this task are presented in ascending order of this key (e.g. sentence length)."""
        return None

    def public_prompt(self, payload: dict[str, Any]) -> dict[str, Any]:
        """The version of the payload shown to the test taker (no answers). Default: everything."""
        return payload

    @abstractmethod
    def clean_answer(self, answer: dict[str, Any]) -> dict[str, Any]:
        """Validate/normalize a submitted answer; raise ValueError if malformed."""

    def render_prompt(self, params: Any, count: int, domain: str, avoid: list[str]) -> str:
        template = Template((PROMPT_DIR / self.prompt_file).read_text())
        avoid_text = "\n".join(f"- {a}" for a in avoid[:AVOID_LIMIT]) or "- (none)"
        values = {"count": str(count), "domain": domain, "avoid": avoid_text, **self.prompt_vars(params, count, avoid)}
        return template.substitute(values)

    def recent_keys(self, db: Session) -> list[str]:
        rows = db.scalars(
            select(Item).where(Item.task_type == self.task_type.value).order_by(Item.id.desc()).limit(AVOID_LIMIT)
        ).all()
        return [self.payload_key(r.payload) for r in rows]

    def payload_key(self, payload: dict[str, Any]) -> str:
        """Content key from a *stored* payload (which may be transformed, so don't re-validate it)."""
        return self.content_key(self.item_model.model_construct(**_item_fields(payload, self.item_model)))

    def generate(self, db: Session, llm: LLMProvider, difficulty: Difficulty, need: int,
                 max_attempts: int = 3) -> list[Item]:
        """Create up to `need`+spare new valid unique items (stored unserved). May return fewer on failure."""
        params = self.params(difficulty)
        created: list[Item] = []
        for _ in range(max_attempts):
            shortfall = need - len(created)
            if shortfall <= 0:
                break
            count = min(self.max_batch, shortfall + (2 if self.max_batch > 1 else 0))
            domain = pick_domain(db, self.task_type)
            prompt = self.render_prompt(params, count, domain, self.recent_keys(db))
            try:
                batch = llm.generate_json(prompt, RawBatch, system=SYSTEM_PROMPT)
            except LLMError as exc:
                log.warning("%s generation failed: %s", self.task_type.value, exc)
                continue
            for raw in batch.items:
                item = self._accept(db, raw, params, difficulty, domain)
                if item is not None:
                    created.append(item)
        return created

    def _accept(self, db: Session, raw: dict[str, Any], params: Any, difficulty: Difficulty,
                domain: str) -> Item | None:
        try:
            parsed = self.item_model.model_validate(raw)
        except ValidationError as exc:
            log.info("%s item rejected by schema: %s", self.task_type.value, str(exc)[:200])
            return None
        problems = self.validate(parsed, params)
        if problems:
            log.info("%s item rejected: %s", self.task_type.value, "; ".join(problems))
            return None
        digest = content_hash(self.task_type, self.content_key(parsed))
        if db.scalar(select(func.count()).select_from(Item).where(Item.content_hash == digest)):
            log.info("%s item rejected: duplicate", self.task_type.value)
            return None
        item = Item(task_type=self.task_type.value, difficulty=difficulty.value, topic=domain,
                    content_hash=digest, payload=self.to_payload(parsed, difficulty), served=False, source="generated")
        db.add(item)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return None
        return item


def _item_fields(payload: dict[str, Any], model: type[BaseModel]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if k in model.model_fields}


MAX_TEXT_CHARS = 20_000


def clean_text_answer(answer: dict[str, Any]) -> dict[str, Any]:
    text = answer.get("text", "")
    if not isinstance(text, str) or len(text) > MAX_TEXT_CHARS:
        raise ValueError("text must be a string")
    return {"text": text}


def shuffled_different(chunks: list[str], forbidden: list[list[str]]) -> list[str]:
    """Shuffle chunks so the result differs from the answer and every acceptable order."""
    rng = random.Random()
    out = list(chunks)
    for _ in range(50):
        rng.shuffle(out)
        if out not in forbidden:
            return out
    return list(reversed(chunks))
