from app.difficulty import BUILD_SENTENCE, DISCUSSION, EMAIL
from app.schemas import BuildSentenceItem, DiscussionItem, EmailItem
from app.spec import Difficulty
from app.validators.build_sentence import validate_build_sentence
from app.validators.write_discussion import validate_discussion
from app.validators.write_email import validate_email
from tests.helpers import bas_item, discussion_item, email_item

B = Difficulty.BEGINNER


def bas(**changes) -> BuildSentenceItem:
    return BuildSentenceItem.model_validate({**bas_item(1), **changes})


def test_build_sentence_valid() -> None:
    assert validate_build_sentence(bas(), BUILD_SENTENCE[B]) == []


def test_build_sentence_rejections() -> None:
    p = BUILD_SENTENCE[B]
    too_few = bas(correct_order=["A", "b", "c."])
    assert any("chunk count" in e for e in validate_build_sentence(too_few, p))
    dup = bas(correct_order=["The", "cat", "sat", "the", "now."])
    assert any("duplicate" in e for e in validate_build_sentence(dup, p))
    no_punct = bas(correct_order=["Tom", "reads", "a book", "in the library", "tonight"])
    assert any("must end" in e for e in validate_build_sentence(no_punct, p))
    mid_punct = bas(correct_order=["Tom.", "reads", "a book", "in the library", "tonight."])
    assert any("inside a non-final" in e for e in validate_build_sentence(mid_punct, p))
    long_sentence = bas(correct_order=["a b c d", "e f g h", "i j k l", "m n o", "p."])
    assert validate_build_sentence(long_sentence, p)


def test_build_sentence_acceptable_orders_must_be_permutations() -> None:
    p = BUILD_SENTENCE[B]
    ok = bas(acceptable_orders=[["tonight.", "Student1", "reads", "a book", "in the library"]])
    assert validate_build_sentence(ok, p) == []
    bad = bas(acceptable_orders=[["different", "chunks", "entirely", "here", "now."]])
    assert any("permutations" in e for e in validate_build_sentence(bad, p))
    assert any("duplicates" in e for e in validate_build_sentence(bas(acceptable_orders=[bas_item(1)["correct_order"]]), p))


def test_email_rules() -> None:
    p = EMAIL[B]
    assert validate_email(EmailItem.model_validate(email_item(1)), p) == []
    short = EmailItem.model_validate({**email_item(1), "scenario": "You must write an email to your teacher about your problem in class, please."})
    assert any("scenario" in e for e in validate_email(short, p))
    one_point = EmailItem.model_validate({**email_item(1), "points": ["a", "b"]})
    assert validate_email(one_point, p) == []


def test_discussion_rules() -> None:
    p = DISCUSSION[B]
    assert validate_discussion(DiscussionItem.model_validate(discussion_item(1)), p) == []
    no_q = DiscussionItem.model_validate({**discussion_item(1), "professor_post": discussion_item(1)["professor_post"].replace("?", ".")})
    assert any("question" in e for e in validate_discussion(no_q, p))
    same = discussion_item(1)
    same["students"][1]["name"] = "Ana"
    assert any("names" in e for e in validate_discussion(DiscussionItem.model_validate(same), p))
