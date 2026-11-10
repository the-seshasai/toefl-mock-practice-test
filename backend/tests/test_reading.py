import pytest

from app.db import SessionLocal
from app.difficulty import ACADEMIC, COMPLETE_WORDS, DAILY_LIFE
from app.generators import REGISTRY
from app.generators.service import fetch_items
from app.llm.fake import FakeProvider
from app.schemas import (
    AcademicPassageItem,
    CompleteWordsItem,
    DailyLifeItem,
    MCQuestion,
)
from app.scoring.reading import score_complete_words, score_mc_set
from app.spec import Difficulty, TaskType
from app.validators.complete_words import locate_blanks, validate_complete_words
from app.validators.mc import validate_questions
from app.validators.read_academic import ACADEMIC_KINDS, validate_academic
from app.validators.read_daily_life import validate_daily_life
from tests.helpers import RoutingFake, ap_item, ctw_item, dl_item

B = Difficulty.BEGINNER


def ctw(**changes) -> CompleteWordsItem:
    return CompleteWordsItem.model_validate({**ctw_item(1), **changes})


def mcq(**changes) -> MCQuestion:
    base = {"prompt": "What is it?", "options": ["a", "b", "c", "d"], "answer": 0, "kind": "detail", "explanation": "Because the text says."}
    return MCQuestion.model_validate({**base, **changes})


# ---------- Complete the Words ----------


def test_ctw_valid_and_blank_rules() -> None:
    p = COMPLETE_WORDS[B]
    assert validate_complete_words(ctw(), p) == []
    first_sentence = ctw(blanks=["Start", *ctw_item(1)["blanks"][:9]])
    assert any("missing" in e for e in validate_complete_words(first_sentence, p))  # first sentence stays intact
    out_of_order = ctw(blanks=list(reversed(ctw_item(1)["blanks"])))
    assert any("out of order" in e for e in validate_complete_words(out_of_order, p))
    assert any("blanks, expected" in e for e in validate_complete_words(ctw(blanks=ctw_item(1)["blanks"][:8]), p))
    dup = ctw(blanks=["alpha"] * 10)
    assert any("distinct" in e for e in validate_complete_words(dup, p))
    short = ctw(blanks=[*ctw_item(1)["blanks"][:9], "it"])
    assert any("at least 3 letters" in e for e in validate_complete_words(short, p))


def test_ctw_adjacent_blanks_rejected() -> None:
    text = "This is the first sentence of the paragraph here. Another sentence follows right after it now. The cat sat quietly."
    item = CompleteWordsItem(text=text, blanks=["Another", "follows", "cat", "sat", "quietly"])
    assert any("adjacent" in e for e in validate_complete_words(item, COMPLETE_WORDS[B].__class__(words=(1, 200), vocabulary="x", blanks=5)))
    assert locate_blanks(text, ["follows", "cat"]) is not None


def test_ctw_payload_segments_reconstruct_text_and_hide_answers() -> None:
    gen = REGISTRY[TaskType.COMPLETE_THE_WORDS]
    payload = gen.to_payload(ctw())
    rebuilt = "".join(
        seg["text"] if "text" in seg else payload["blanks"][seg["blank"]]["answer"] for seg in payload["segments"]
    )
    assert rebuilt == payload["text"]
    for b in payload["blanks"]:
        assert b["prefix"] + "x" * b["missing"] and len(b["prefix"]) == (len(b["answer"]) + 1) // 2
    public = gen.public_prompt(payload)
    assert "blanks" not in public and all("answer" not in s for s in public["segments"])


def test_ctw_scoring() -> None:
    payload = REGISTRY[TaskType.COMPLETE_THE_WORDS].to_payload(ctw())
    missing = [b["answer"][len(b["prefix"]):] for b in payload["blanks"]]
    assert score_complete_words(payload, {"letters": missing})[0] == 10.0
    upper = [m.upper() for m in missing]
    assert score_complete_words(payload, {"letters": upper})[0] == 10.0  # case-insensitive
    half = [*missing[:4], *[""] * 6]
    pts, mx, fb = score_complete_words(payload, {"letters": half})
    assert (pts, mx) == (4.0, 10.0) and fb["blanks"][5]["correct"] is False
    assert score_complete_words(payload, None)[0] == 0.0
    wrong = ["zz"] * 10
    assert score_complete_words(payload, {"letters": wrong})[0] == 0.0


# ---------- multiple choice validation ----------


def test_mc_rules() -> None:
    kinds = frozenset({"detail", "main_idea", "vocabulary", "inference"})
    good = [mcq(), mcq(prompt="Other question?", kind="main_idea")]
    assert validate_questions(good, (2, 3), kinds, "text", 2) == []
    assert any("distinct" in e for e in validate_questions([mcq(options=["a", "a", "c", "d"]), good[1]], (2, 3), kinds, "t", 2))
    assert any("above" in e for e in validate_questions([mcq(options=["a", "b", "c", "None of the above"]), good[1]], (2, 3), kinds, "t", 2))
    assert any("unknown kind" in e for e in validate_questions([mcq(kind="trivia"), good[1]], (2, 3), kinds, "t", 1))
    assert any("different question kinds" in e for e in validate_questions([mcq(), mcq(prompt="Another one?")], (2, 3), kinds, "t", 2))
    assert any("duplicate" in e for e in validate_questions([mcq(), mcq(kind="main_idea")], (2, 3), kinds, "t", 2))
    vocab = mcq(prompt="The word 'nectar' means", kind="vocabulary")
    assert any("quote a word" in e for e in validate_questions([vocab, good[1]], (2, 3), kinds, "no such term here", 2))
    assert validate_questions([vocab, good[1]], (2, 3), kinds, "sweet nectar here", 2) == []
    assert any("questions, expected" in e for e in validate_questions(good[:1], (2, 3), kinds, "t", 1))


def test_answer_index_bounds_enforced_by_schema() -> None:
    with pytest.raises(ValueError):
        mcq(answer=4)
    with pytest.raises(ValueError):
        mcq(options=["a", "b", "c"])


def test_daily_life_and_academic_word_ranges() -> None:
    dl = DailyLifeItem.model_validate(dl_item(1))
    assert validate_daily_life(dl, DAILY_LIFE[B]) == []
    short = DailyLifeItem.model_validate({**dl_item(1), "text": "Too short to count as a real daily life text at all."})
    assert any("words, expected" in e for e in validate_daily_life(short, DAILY_LIFE[B]))
    ap = AcademicPassageItem.model_validate(ap_item(1))
    assert validate_academic(ap, ACADEMIC[B]) == []
    one_para = AcademicPassageItem.model_validate({**ap_item(1), "passage": ap.passage.replace("\n\n", " ")})
    assert any("two paragraphs" in e for e in validate_academic(one_para, ACADEMIC[B]))
    assert "main_idea" in ACADEMIC_KINDS


# ---------- generators ----------


def test_mc_payload_shuffles_options_and_rekeys_answer() -> None:
    gen = REGISTRY[TaskType.READ_ACADEMIC]
    item = AcademicPassageItem.model_validate(ap_item(1))
    positions = set()
    for _ in range(40):
        payload = gen.to_payload(item)
        for q in payload["questions"]:
            assert q["options"][q["answer"]] == "right answer" and sorted(q["options"]) == sorted(item.questions[0].options)
            positions.add(q["answer"])
    assert len(positions) > 1  # the correct answer does not always sit in the same slot
    public = gen.public_prompt(payload)
    assert all(set(q) == {"prompt", "options"} for q in public["questions"])


def test_reading_generators_produce_unique_valid_items() -> None:
    with SessionLocal() as db:
        for task, factory in ((TaskType.COMPLETE_THE_WORDS, ctw_item), (TaskType.READ_DAILY_LIFE, dl_item), (TaskType.READ_ACADEMIC, ap_item)):
            bad = {"topic": "x"}
            items = REGISTRY[task].generate(db, FakeProvider([{"items": [factory(), bad, factory()]}]), B, need=2)
            assert len(items) == 2 and items[0].content_hash != items[1].content_hash


def test_reading_fetch_falls_back_to_seeds() -> None:
    llm = RoutingFake(fail_generation=True)
    with SessionLocal() as db:
        for task, n in ((TaskType.COMPLETE_THE_WORDS, 3), (TaskType.READ_DAILY_LIFE, 3), (TaskType.READ_ACADEMIC, 2)):
            items, warnings = fetch_items(db, llm, task, B, n)
            assert len(items) == n and warnings


# ---------- answers ----------


def test_clean_answer_validation() -> None:
    ctw_gen = REGISTRY[TaskType.COMPLETE_THE_WORDS]
    assert ctw_gen.clean_answer({"letters": ["ab", ""]}) == {"letters": ["ab", ""]}
    for bad in ({"letters": "abc"}, {"letters": [1]}, {"letters": ["x" * 50]}):
        with pytest.raises(ValueError):
            ctw_gen.clean_answer(bad)
    mc_gen = REGISTRY[TaskType.READ_ACADEMIC]
    assert mc_gen.clean_answer({"choices": [0, None, 3]}) == {"choices": [0, None, 3]}
    for bad in ({"choices": [4]}, {"choices": ["a"]}, {"choices": [True]}, {"choices": "x"}):
        with pytest.raises(ValueError):
            mc_gen.clean_answer(bad)


def test_mc_scoring() -> None:
    payload = REGISTRY[TaskType.READ_ACADEMIC].to_payload(AcademicPassageItem.model_validate(ap_item(1)))
    right = [q["answer"] for q in payload["questions"]]
    assert score_mc_set(payload, {"choices": right})[0] == 5.0
    pts, mx, fb = score_mc_set(payload, {"choices": [right[0], (right[1] + 1) % 4]})
    assert (pts, mx) == (1.0, 5.0) and fb["questions"][1]["correct"] is False and fb["questions"][4]["chosen"] is None
    assert score_mc_set(payload, None)[0] == 0.0


def test_prompt_aims_inside_the_allowed_range() -> None:
    from app.generators.base import aim

    assert aim((110, 170)) == ("122", "158")
    lo, hi = aim((50, 75))
    assert 50 < int(lo) < int(hi) < 75


def test_vocabulary_question_accepts_quoted_phrases_and_ignores_possessives() -> None:
    kinds = frozenset({"vocabulary", "detail", "main_idea"})
    other = mcq(prompt="Another question?", kind="detail")
    source = "A forest acts as a carbon sink because trees store carbon. The professor argues this matters."

    def vocab(prompt: str) -> MCQuestion:
        return mcq(prompt=prompt, kind="vocabulary")

    assert validate_questions([vocab("What does the phrase 'carbon sink' mean?"), other], (2, 3), kinds, source, 2) == []
    assert validate_questions([vocab("In the professor's talk, the word \"sink\" is closest to"), other], (2, 3), kinds, source, 2) == []
    assert any("quote" in e for e in validate_questions([vocab("What does the professor's idea mean?"), other], (2, 3), kinds, source, 2))
    assert any("quote" in e for e in validate_questions([vocab("What does 'glacier ice' mean?"), other], (2, 3), kinds, source, 2))
