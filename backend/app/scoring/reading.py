"""Machine scoring for Reading: Complete the Words (1 point per blank) and multiple-choice sets (1 point per question)."""
from typing import Any


def score_complete_words(payload: dict[str, Any], answer: dict[str, Any] | None) -> tuple[float, float, dict[str, Any]]:
    typed_all = [str(s) for s in (answer or {}).get("letters", [])]
    results: list[dict[str, Any]] = []
    for i, blank in enumerate(payload["blanks"]):
        typed = typed_all[i].strip() if i < len(typed_all) else ""
        full = blank["prefix"] + typed
        correct = typed != "" and full.lower() == blank["answer"].lower()
        results.append({"prefix": blank["prefix"], "answer": blank["answer"], "typed": typed, "correct": correct})
    points = float(sum(r["correct"] for r in results))
    return points, float(len(results)), {"blanks": results, "correct_count": int(points), "total": len(results)}


def score_mc_set(payload: dict[str, Any], answer: dict[str, Any] | None) -> tuple[float, float, dict[str, Any]]:
    choices = list((answer or {}).get("choices", []))
    results: list[dict[str, Any]] = []
    for i, q in enumerate(payload["questions"]):
        chosen = choices[i] if i < len(choices) else None
        results.append({"chosen": chosen, "correct_index": q["answer"], "correct": chosen == q["answer"],
                        "explanation": q["explanation"], "kind": q.get("kind", "")})
    points = float(sum(r["correct"] for r in results))
    return points, float(len(results)), {"questions": results, "correct_count": int(points), "total": len(results)}
