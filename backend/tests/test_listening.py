import wave

import pytest

from app.audio.builder import AudioBuilder, script_key
from app.audio.voices import VOICES, AudioUnavailable, assign_script_voices, pick_voices
from app.db import SessionLocal
from app.difficulty import ACADEMIC_TALK, ANNOUNCEMENT, CONVERSATION, LISTEN_REPLY
from app.generators import REGISTRY
from app.schemas import ConversationItem, ListenReplyItem, MonologueItem
from app.spec import Difficulty, TaskType
from app.validators.listening import (
    validate_conversation,
    validate_listen_reply,
    validate_monologue,
)
from tests.helpers import FakeTTS, ann_item, conv_item, lcr_item, talk_item

B = Difficulty.BEGINNER


# ---------- validators ----------


def test_listen_reply_rules() -> None:
    p = LISTEN_REPLY[B]
    assert validate_listen_reply(ListenReplyItem.model_validate(lcr_item(1)), p) == []
    long = ListenReplyItem.model_validate({**lcr_item(1), "utterance": "Would you like some tea or coffee or juice or water or milk today?"})
    assert any("words, expected" in e for e in validate_listen_reply(long, p))
    stage = ListenReplyItem.model_validate({**lcr_item(1), "utterance": "(smiling) Would you like tea?"})
    assert any("brackets" in e for e in validate_listen_reply(stage, p))
    dup = ListenReplyItem.model_validate({**lcr_item(1), "options": ["Yes.", "yes.", "No.", "Maybe."]})
    assert any("distinct" in e for e in validate_listen_reply(dup, p))
    wordy = ListenReplyItem.model_validate({**lcr_item(1), "options": ["word " * 20, "b", "c", "d"]})
    assert any("too long" in e for e in validate_listen_reply(wordy, p))


def test_conversation_rules() -> None:
    p = CONVERSATION[B]
    assert validate_conversation(ConversationItem.model_validate(conv_item(1)), p) == []
    one_sided = {**conv_item(1), "lines": [{"speaker": 0, "text": "Hello there my friend how are you doing today at school."}] * 5 + [{"speaker": 1, "text": "Fine thanks."}]}
    assert any("at least twice" in e for e in validate_conversation(ConversationItem.model_validate(one_sided), p))
    wrong_start = {**conv_item(1), "lines": [{"speaker": 1 - (i % 2), "text": "Hello, I need some help with the project today please."} for i in range(6)]}
    assert any("must start" in e for e in validate_conversation(ConversationItem.model_validate(wrong_start), p))
    short = {**conv_item(1), "lines": [{"speaker": i % 2, "text": "Hi there."} for i in range(6)]}
    assert any("words, expected" in e for e in validate_conversation(ConversationItem.model_validate(short), p))


def test_monologue_rules() -> None:
    assert validate_monologue(MonologueItem.model_validate(ann_item(1)), ANNOUNCEMENT[B], 2) == []
    assert validate_monologue(MonologueItem.model_validate(talk_item(1)), ACADEMIC_TALK[B], 3) == []
    two_kinds = MonologueItem.model_validate({**talk_item(1), "questions": talk_item(1)["questions"][:2] + [talk_item(1)["questions"][1]]})
    assert any("kinds" in e or "duplicate" in e for e in validate_monologue(two_kinds, ACADEMIC_TALK[B], 3))
    md = MonologueItem.model_validate({**ann_item(1), "text": "**Bold** announcement " + ann_item(1)["text"]})
    assert any("markdown" in e for e in validate_monologue(md, ANNOUNCEMENT[B], 2))


# ---------- generators ----------


def test_payloads_hide_script_and_carry_genders_not_voices() -> None:
    gen = REGISTRY[TaskType.LISTEN_CONVERSATION]
    payload = gen.to_payload(ConversationItem.model_validate(conv_item(1)), B)
    assert [line["gender"] for line in payload["script"][:2]] == ["female", "male"]
    assert all("voice" not in line for line in payload["script"]) and "audio_key" not in payload
    public = gen.public_prompt(payload)
    assert set(public) == {"setting", "has_audio", "questions"} and "script" not in str(public)
    assert payload["length_scale"] == CONVERSATION[B].length_scale


def test_listening_generation_and_recent_keys() -> None:
    from app.llm.fake import FakeProvider

    with SessionLocal() as db:
        for task, factory in ((TaskType.LISTEN_CHOOSE_RESPONSE, lcr_item), (TaskType.LISTEN_CONVERSATION, conv_item),
                              (TaskType.LISTEN_ANNOUNCEMENT, ann_item), (TaskType.LISTEN_ACADEMIC_TALK, talk_item)):
            gen = REGISTRY[task]
            first = gen.generate(db, FakeProvider([{"items": [factory(), {"bogus": 1}]}]), B, need=1)
            second = gen.generate(db, FakeProvider([{"items": [factory()]}]), B, need=1)  # exercises payload_key via recent_keys
            assert len(first) == 1 and len(second) == 1
            assert gen.payload_key(first[0].payload) in gen.recent_keys(db)


# ---------- audio ----------


def script_of(*lines: tuple[str, str, str]) -> list[dict]:
    return [{"speaker": s, "voice": v, "text": t} for s, v, t in lines]


def test_builder_groups_by_voice_caches_and_joins(tmp_path) -> None:
    tts = FakeTTS()
    builder = AudioBuilder(tts, tmp_path)
    s1 = script_of(("A", "en_US-ryan-medium", "Hello there."), ("B", "en_US-amy-medium", "Hi, how are you?"))
    s2 = script_of(("A", "en_US-amy-medium", "Second script."), ("B", "en_US-ryan-medium", "Goes here."))
    paths = builder.build_many([(s1, 1.0), (s2, 1.0)])
    voices_in_order = [c[0] for c in tts.calls]
    assert voices_in_order == sorted(voices_in_order)  # each voice's segments are synthesized together (one model load)
    assert all(p.exists() for p in paths) and paths[0] != paths[1]
    with wave.open(str(paths[0])) as w:
        frames = w.getnframes()
        assert w.getnchannels() == 1 and w.getsampwidth() == 2 and w.getframerate() == 22050
    speech = (len("Hello there.") + len("Hi, how are you?")) * 40
    assert frames == speech + int(22050 * 0.45)  # two segments + one pause
    n = len(tts.calls)
    builder.build_many([(s1, 1.0)])
    assert len(tts.calls) == n  # cache hit: nothing re-synthesized


def test_script_key_depends_on_voice_text_and_rate() -> None:
    base = script_of(("A", "en_US-ryan-medium", "Hello."))
    assert script_key(base, 1.0) == script_key(base, 1.0)
    assert script_key(base, 1.0) != script_key(base, 1.15)
    assert script_key(base, 1.0) != script_key(script_of(("A", "en_US-amy-medium", "Hello.")), 1.0)
    assert script_key(base, 1.0) != script_key(script_of(("A", "en_US-ryan-medium", "Hello!")), 1.0)


def test_voice_assignment() -> None:
    names = [v.name for v in VOICES]
    for _ in range(30):
        script = [{"speaker": "Ana", "gender": "female", "text": "x"}, {"speaker": "Ben", "gender": "male", "text": "y"},
                  {"speaker": "Ana", "gender": "female", "text": "z"}]
        assign_script_voices(script, names)
        assert script[0]["voice"] == script[2]["voice"] != script[1]["voice"]
        two_women = pick_voices(["female", "female"], names)
        assert two_women[0] != two_women[1]
    only_one = pick_voices(["male", "female"], ["en_US-ryan-medium"])
    assert only_one == ["en_US-ryan-medium", "en_US-ryan-medium"]  # degrades gracefully with a single voice
    with pytest.raises(AudioUnavailable):
        pick_voices(["male"], [])


def test_real_piper_synthesis_if_voices_installed() -> None:
    from pathlib import Path

    from app.audio.tts import PiperSynthesizer

    voice_dir = Path(__file__).resolve().parents[2] / "data" / "piper"
    tts = PiperSynthesizer(voice_dir)
    if not tts.available_voices():
        pytest.skip("Piper voices not installed")
    slow = tts.synth(tts.available_voices()[0], "The reading room closes at nine tonight.", 1.15)
    fast = tts.synth(tts.available_voices()[0], "The reading room closes at nine tonight.", 0.9)
    assert len(slow) > 20_000 and len(slow) > len(fast)  # length_scale really changes speech rate
    assert tts.available_voices() == [v.name for v in VOICES if v.name in tts.available_voices()]

