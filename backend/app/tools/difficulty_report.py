"""Measure how hard the generated items really are, per task and level, to tune the difficulty tables.

    python -m app.tools.difficulty_report                 # report on every item already in the database
    python -m app.tools.difficulty_report --sample 2      # first generate 2 items per task and level with the LLM
"""
import argparse
import re
import statistics
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from sqlalchemy import select

from app.db import SessionLocal, init_db
from app.generators import REGISTRY
from app.models import Item
from app.spec import LEVELS, TaskType
from app.validators.readability import fk_grade

SAMPLE_TASKS = (TaskType.COMPLETE_THE_WORDS, TaskType.READ_DAILY_LIFE, TaskType.READ_ACADEMIC, TaskType.LISTEN_CONVERSATION,
                TaskType.LISTEN_ACADEMIC_TALK, TaskType.WRITE_ACADEMIC_DISCUSSION)


def text_of(task_type: str, p: dict[str, Any]) -> str:
    """The reading/listening text whose difficulty we measure."""
    if "passage" in p:
        return p["passage"]
    if "script" in p:
        return " ".join(line["text"] for line in p["script"])
    if "questions" in p and task_type == TaskType.TAKE_INTERVIEW.value:
        return " ".join(p["questions"])
    if "professor_post" in p:
        return p["professor_post"] + " " + " ".join(s["text"] for s in p["students"])
    if "scenario" in p:
        return p["scenario"]
    if "sentence" in p:
        return p["sentence"]
    if "correct_order" in p:
        return " ".join(p["correct_order"])
    return p.get("text", "")


def avg(values: list[float]) -> float:
    return round(statistics.mean(values), 1) if values else 0.0


def report(db, sources: tuple[str, ...] = ("generated", "seed"), min_id: int = 0, tasks: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[Item]] = defaultdict(list)
    for item in db.scalars(select(Item).where(Item.source.in_(sources), Item.id > min_id)):
        if tasks and item.task_type not in tasks:
            continue
        groups[(item.task_type, item.difficulty)].append(item)
    rows = []
    for (task, level), items in sorted(groups.items()):
        texts = [text_of(task, i.payload) for i in items]
        words = [len(t.split()) for t in texts]
        rows.append({"task": task, "level": level, "n": len(items), "words": avg(words), "fk": avg([fk_grade(t) for t in texts]),
                     "sentence_len": avg([len(t.split()) / max(len(re.findall(r"[.!?]+(?:\s|$)", t)), 1) for t in texts])})
    return rows


def monotonic_warnings(rows: list[dict[str, Any]], key: str = "fk") -> list[str]:
    out = []
    for task in sorted({r["task"] for r in rows}):
        by_level = {r["level"]: r[key] for r in rows if r["task"] == task and r["n"] >= 1}
        ordered = [by_level[lv.value] for lv in LEVELS if lv.value in by_level]
        if ordered != sorted(ordered):
            out.append(f"{task}: {key} does not rise with level -> {by_level}")
    return out


def sample(per_level: int, tasks: tuple[TaskType, ...] = SAMPLE_TASKS, workers: int = 3) -> None:
    from app.runtime import get_llm

    def one(task: TaskType, level) -> str:
        with SessionLocal() as db:
            made = REGISTRY[task].generate(db, get_llm(), level, need=per_level)
        return f"{task.value}/{level.value}: {len(made)} new"

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for line in pool.map(lambda a: one(*a), [(t, lv) for t in tasks for lv in LEVELS]):
            print(" ", line, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", type=int, default=0, help="generate N items per task and level first (uses the LLM)")
    parser.add_argument("--tasks", nargs="*", default=[], help="restrict to these task types")
    parser.add_argument("--new-only", action="store_true", help="report only items created by this run's --sample")
    parser.add_argument("--generated-only", action="store_true", help="ignore the hand-written seed bank")
    args = parser.parse_args()
    init_db()
    with SessionLocal() as db:
        last_id = db.scalar(select(Item.id).order_by(Item.id.desc()).limit(1)) or 0
    if args.sample:
        print("Generating samples...")
        sample(args.sample, tuple(TaskType(t) for t in args.tasks) or SAMPLE_TASKS)
    with SessionLocal() as db:
        rows = report(db, ("generated",) if args.generated_only or args.new_only else ("generated", "seed"),
                      min_id=last_id if args.new_only else 0, tasks=tuple(args.tasks))
    print(f"\n{'task':28} {'level':13} {'n':>3} {'words':>6} {'FK grade':>9} {'words/sentence':>15}")
    for r in rows:
        print(f"{r['task']:28} {r['level']:13} {r['n']:>3} {r['words']:>6} {r['fk']:>9} {r['sentence_len']:>15}")
    for key in ("words", "fk"):
        for w in monotonic_warnings(rows, key):
            print("WARNING", w)


if __name__ == "__main__":
    main()
