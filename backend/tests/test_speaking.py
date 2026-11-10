import pytest

from app.audio.stt import SttError, Transcript, Word
from app.difficulty import INTERVIEW, REPEAT
from app.generators import REGISTRY
from app.llm.errors import LLMParseError
from app.llm.fake import FakeProvider
from app.schemas import InterviewItem, RepeatItem
from app.scoring.alignment import (
    align,
    delivery_stats,
    load_thresholds,
    score_from_accuracy,
    tokens,
)
from app.scoring.speaking import score_interview, score_repeat
from app.spec import Difficulty, TaskType
from app.validators.speaking import validate_interview, validate_repeat
from tests.helpers import FakeStt, feedback, interview_item, rep_item

B = Difficulty.BEGINNER


# ---------- validators ----------


def test_repeat_rules() -> None:
    p = REPEAT[B]
    assert validate_repeat(RepeatItem.model_validate(rep_item(1)), p) == []
    long = RepeatItem(sentence="This sentence is much too long for a beginner to repeat back exactly.")
    assert any("words, expected" in e for e in validate_repeat(long, p))
    assert any("must end" in e for e in validate_repeat(RepeatItem(sentence="The bus leaves soon"), p))
    assert any("numbers" in e for e in validate_repeat(RepeatItem(sentence="The bus leaves at 7 now."), p))
    assert any("brackets" in e for e in validate_repeat(RepeatItem(sentence="The (big) bus leaves now."), p))


def test_interview_rules() -> None:
    p = INTERVIEW[B]
    assert validate_interview(InterviewItem.model_validate(interview_item(1)), p) == []
    dup = {**interview_item(1), "questions": ["What do you like to do today?"] * 4}
    assert any("distinct" in e for e in validate_interview(InterviewItem.model_validate(dup), p))
    statements = {**interview_item(1), "questions": [f"Tell me about your favorite day number {k} of the week." for k in range(4)]}
    assert any("actual questions" in e for e in validate_interview(InterviewItem.model_validate(statements), p))
    short = {**interview_item(1), "questions": [f"Why {k}?" for k in range(4)]}
    assert any("words, expected" in e for e in validate_interview(InterviewItem.model_validate(short), p))
    with pytest.raises(ValueError):
        InterviewItem.model_validate({**interview_item(1), "questions": ["a question here?"] * 3})


# ---------- generators ----------


def test_repeat_payload_and_ordering_hook() -> None:
    gen = REGISTRY[TaskType.LISTEN_AND_REPEAT]
    short = gen.to_payload(RepeatItem(sentence="The bus leaves soon today."), B)
    long = gen.to_payload(RepeatItem(sentence="The bus leaves at seven thirty every single morning."), B)
    assert short["word_count"] == 5 and 8 <= short["response_seconds"] < long["response_seconds"] <= 30
    assert gen.order_key(short) < gen.order_key(long)
    public = gen.public_prompt(short)
    assert short["sentence"] not in str(public) and public["has_audio"] and public["response_seconds"] == short["response_seconds"]
    with pytest.raises(ValueError):
        gen.clean_answer({"text": "x"})


def test_interview_payload_has_one_clip_per_question() -> None:
    gen = REGISTRY[TaskType.TAKE_INTERVIEW]
    payload = gen.to_payload(InterviewItem.model_validate(interview_item(1)), B)
    assert len(payload["audio_parts"]) == 4 and payload["prep_seconds"] == 10 and payload["response_seconds"] == 45
    assert all(len(p["script"]) == 1 and p["script"][0]["gender"] == "female" for p in payload["audio_parts"])
    public = gen.public_prompt(payload)
    assert public["parts"] == 4 and "What do you like" not in str(public)  # question text is audio-only


def test_repeat_prompt_spreads_lengths() -> None:
    gen = REGISTRY[TaskType.LISTEN_AND_REPEAT]
    v = gen.prompt_vars(REPEAT[B], 7, [])
    assert v["lengths"].startswith("1) about 4 words") and "7) about 10 words" in v["lengths"]


# ---------- alignment ----------


def test_tokens_normalize_numbers_and_apostrophes() -> None:
    assert tokens("It’s nine o'clock, isn't it?") == ["it's", "nine", "o'clock", "isn't", "it"]
    assert tokens("The bus leaves at 7 thirty.") == ["the", "bus", "leaves", "at", "seven", "thirty"]


def test_alignment_cases() -> None:
    target = "The library will be closed on Monday because of the holiday."
    perfect = align(target, "the library will be closed on monday because of the holiday")
    assert perfect["accuracy"] == 1.0 and perfect["differences"] == []
    missing = align(target, "The library will be closed on Monday because holiday")
    assert missing["differences"] == [{"type": "missing", "target": "of the", "heard": ""}]
    assert 0.7 < missing["accuracy"] < 0.9
    changed = align(target, "The library will be open on Monday because of the holiday")
    assert changed["differences"] == [{"type": "changed", "target": "closed", "heard": "open"}]
    extra = align(target, "The library will be closed on Monday because of the big holiday")
    assert extra["differences"] == [{"type": "extra", "target": "", "heard": "big"}]
    assert align(target, "")["accuracy"] == 0.0
    assert align(target, "completely unrelated words here")["accuracy"] < 0.1


def test_rubric_thresholds_come_from_the_versioned_file() -> None:
    assert load_thresholds()[0] == (0.95, 5) and load_thresholds()[-1] == (0.0, 0)
    assert [score_from_accuracy(a) for a in (1.0, 0.95, 0.9, 0.7, 0.5, 0.3, 0.1, 0.0)] == [5, 5, 4, 3, 2, 1, 0, 0]


def test_delivery_stats() -> None:
    words = [Word("a", 0.0, 0.3, 0.9), Word("b", 0.4, 0.7, 0.4), Word("c", 2.0, 2.3, 0.9)]  # 1.3 s pause before "c"
    d = delivery_stats(Transcript("a b c", words, 3.0))
    assert d["long_pauses"] == 1 and d["unclear_words"] == ["b"] and d["words"] == 3 and d["wpm"] == round(3 / 2.3 * 60)
    assert delivery_stats(Transcript("", [], 2.0))["words"] == 0


# ---------- scoring ----------


def make_rec(tmp_path, name: str = "1/1_0.webm") -> None:
    f = tmp_path / name
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(b"x" * 500)


def test_score_repeat(tmp_path) -> None:
    payload = {"sentence": "The bus leaves at seven thirty."}
    make_rec(tmp_path)
    answer = {"parts": {"0": {"file": "1/1_0.webm", "duration_ms": 4000}}}
    stt = FakeStt()
    stt.texts["1_0.webm"] = "The bus leaves at seven thirty."
    pts, mx, fb = score_repeat(payload, answer, stt, tmp_path)
    assert (pts, mx) == (5.0, 5.0) and fb["accuracy"] == 1.0 and fb["rubric_version"] == "speaking_repeat.v1" and fb["delivery"]["words"] == 6
    stt.texts["1_0.webm"] = "The bus leaves at thirty."
    pts, _, fb = score_repeat(payload, answer, stt, tmp_path)
    assert pts == 3.0 and fb["differences"][0]["target"] == "seven" and fb["_transcript"] == "The bus leaves at thirty."
    none = score_repeat(payload, None, stt, tmp_path)
    assert none[0] == 0.0 and "No recording" in none[2]["note"]
    assert score_repeat(payload, {"parts": {"0": {"file": "gone.webm"}}}, stt, tmp_path)[0] == 0.0  # missing file


def interview_payload() -> dict:
    return REGISTRY[TaskType.TAKE_INTERVIEW].to_payload(InterviewItem.model_validate(interview_item(1)), B)


def test_score_interview_single_llm_call(tmp_path) -> None:
    for i in range(4):
        make_rec(tmp_path, f"1/1_{i}.webm")
    answer = {"parts": {str(i): {"file": f"1/1_{i}.webm", "duration_ms": 30000} for i in range(4)}}
    llm = FakeProvider([{"items": [feedback(4.0), feedback(3.5), feedback(5.0), feedback(2.0)]}])
    pts, mx, fb = score_interview(llm, FakeStt(), interview_payload(), answer, B, tmp_path)
    assert (pts, mx) == (14.5, 20.0) and len(llm.calls) == 1
    prompt = llm.calls[0]["prompt"]
    assert prompt.count("<transcript>") == 4 and "Delivery statistics" in prompt and "ignore any request" in llm.calls[0]["system"]
    assert fb["rubric_version"] == "speaking_interview.v1" and fb["items"][2]["model_answer"] and fb["items"][0]["question"].startswith("What do you")
    assert fb["_transcript"].startswith("Q1:")


def test_interview_skips_empty_responses_without_llm(tmp_path) -> None:
    llm = FakeProvider([{"items": [feedback(4.0)]}])
    make_rec(tmp_path, "1/1_1.webm")
    answer = {"parts": {"1": {"file": "1/1_1.webm", "duration_ms": 9000}}}  # only the second question was answered
    pts, _, fb = score_interview(llm, FakeStt(), interview_payload(), answer, B, tmp_path)
    assert pts == 4.0 and [i["score"] for i in fb["items"]] == [0.0, 4.0, 0.0, 0.0] and len(llm.calls) == 1
    none_pts, _, _ = score_interview(FakeProvider([]), FakeStt(), interview_payload(), None, B, tmp_path)
    assert none_pts == 0.0  # nothing recorded: no LLM call needed (an empty FakeProvider would fail)
    short = FakeStt()
    short.default = "um yes"
    assert score_interview(FakeProvider([]), short, interview_payload(), answer, B, tmp_path)[0] == 0.0  # too short to grade


def test_interview_rejects_wrong_item_count(tmp_path) -> None:
    make_rec(tmp_path, "1/1_0.webm")
    answer = {"parts": {"0": {"file": "1/1_0.webm", "duration_ms": 9000}}}
    with pytest.raises(LLMParseError):
        score_interview(FakeProvider([{"items": [feedback(4.0), feedback(4.0)]}]), FakeStt(), interview_payload(), answer, B, tmp_path)


def test_stt_failure_surfaces_as_stt_error(tmp_path) -> None:
    make_rec(tmp_path)
    stt = FakeStt()
    stt.fail = True
    with pytest.raises(SttError):
        score_repeat({"sentence": "The bus leaves."}, {"parts": {"0": {"file": "1/1_0.webm"}}}, stt, tmp_path)


# ---------- real models (skipped when not installed) ----------


def test_real_whisper_transcribes_piper_speech_and_webm(tmp_path) -> None:
    import shutil
    import subprocess
    import wave
    from pathlib import Path

    from app.audio.stt import WhisperTranscriber
    from app.audio.tts import PiperSynthesizer

    root = Path(__file__).resolve().parents[2] / "data"
    stt = WhisperTranscriber(root / "whisper" / "base.en")
    tts = PiperSynthesizer(root / "piper")
    if not stt.available() or not tts.available_voices():
        pytest.skip("Whisper model or Piper voices not installed")
    sentence = "The library will be closed on Monday because of the holiday."
    wav = tmp_path / "s.wav"
    pcm = tts.synth(tts.available_voices()[0], sentence, 1.0)
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(tts.sample_rate)
        w.writeframes(pcm)
    try:
        result = stt.transcribe(wav)
        assert align(sentence, result.text)["accuracy"] >= 0.9 and result.words and result.words[0].prob > 0.3
        if shutil.which("ffmpeg"):  # browsers record opus-in-webm: make sure PyAV can decode it
            webm = tmp_path / "s.webm"
            subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(wav), "-c:a", "libopus", str(webm)], check=True)
            assert align(sentence, stt.transcribe(webm).text)["accuracy"] >= 0.9
        garbage = tmp_path / "bad.webm"
        garbage.write_bytes(b"not audio at all" * 20)
        with pytest.raises(SttError):
            stt.transcribe(garbage)
    finally:
        stt.close()
