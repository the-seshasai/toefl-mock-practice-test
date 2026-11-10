"""Shared test doubles: a prompt-routing fake LLM and item factories valid for Beginner difficulty."""
import itertools
import json
from typing import Any

from app.llm.base import LLMProvider

_counter = itertools.count(1)


def bas_item(n: int | None = None) -> dict[str, Any]:
    n = n or next(_counter)
    return {
        "context": f"What does student {n} do at night?",
        "correct_order": [f"Student{n}", "reads", "a book", "in the library", "tonight."],
        "acceptable_orders": [],
        "explanation": "Subject, verb, object, place, then time.",
        "topic": "reading",
    }


def email_item(n: int | None = None) -> dict[str, Any]:
    n = n or next(_counter)
    return {
        "topic": f"topic {n}", "recipient": "your teacher",
        "scenario": f"Scenario {n}: " + " ".join(["you"] * 8) + " need help with a problem in class so write an email to your teacher about it today.",
        "points": ["Explain the problem", "Ask for help"],
    }


def discussion_item(n: int | None = None) -> dict[str, Any]:
    n = n or next(_counter)
    return {
        "topic": f"topic {n}", "professor_name": "Dr. Lee",
        "professor_post": f"Post {n}: we are discussing school life this week and I would like to hear your views on it. What do you think is best for students?",
        "students": [
            {"name": "Ana", "text": "I think schools should change this rule because students need more freedom and choice in how they spend their days."},
            {"name": "Ben", "text": "I disagree with Ana because rules help students stay focused and they make the school safer for every single person."},
        ],
    }


def _mcq(prompt: str, kind: str) -> dict[str, Any]:
    return {"prompt": prompt, "options": ["right answer", "wrong one", "wrong two", "wrong three"], "answer": 0,
            "kind": kind, "explanation": "Because the text says so directly."}


BLANK_WORDS = ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel", "india", "juliet"]


def ctw_item(n: int | None = None) -> dict[str, Any]:
    n = n or next(_counter)
    text = f"Start {n} is the first sentence of this short test paragraph for students. " + " ".join(
        f"We saw the {w} again." for w in BLANK_WORDS
    )
    return {"topic": f"topic {n}", "text": text, "blanks": list(BLANK_WORDS)}


def dl_item(n: int | None = None) -> dict[str, Any]:
    n = n or next(_counter)
    return {
        "topic": f"topic {n}", "format": "a notice", "title": f"Notice {n}",
        "text": f"Notice {n}: the office will close early on Friday because of a meeting. Please collect your forms before noon "
                "and leave them with the front desk if you cannot return before the doors close at the end of the day.",
        "questions": [_mcq("Why will the office close early?", "detail"), _mcq("What is the main purpose of this notice?", "main_purpose")],
    }


def ap_item(n: int | None = None) -> dict[str, Any]:
    n = n or next(_counter)
    p1 = f"Passage {n} explains how bees collect nectar from flowers. " + " ".join(["The process is simple and happens every day."] * 8)
    p2 = "Scientists study this behavior closely. " + " ".join(["They record how often bees visit each flower."] * 8)
    return {
        "topic": f"topic {n}", "title": f"Bees {n}", "passage": f"{p1}\n\n{p2}",
        "questions": [_mcq("What is the passage mainly about?", "main_idea"), _mcq("What do bees collect?", "detail"),
                      _mcq("The word 'nectar' is closest in meaning to", "vocabulary"), _mcq("What can be inferred?", "inference"),
                      _mcq("Which is NOT mentioned?", "negative_detail")],
    }


def lcr_item(n: int | None = None) -> dict[str, Any]:
    n = n or next(_counter)
    return {"topic": f"tea {n}", "utterance": f"Would you like some tea number {n} today?",
            "options": ["Yes, please, that sounds lovely.", "I walked to school.", "It is on the table.", "No, it was yesterday."],
            "answer": 0, "explanation": "An offer is answered by accepting or refusing it."}


def conv_item(n: int | None = None) -> dict[str, Any]:
    n = n or next(_counter)
    lines = [{"speaker": i % 2, "text": f"Hello, I need some help with project {n} today please."} for i in range(6)]
    return {"topic": f"project {n}", "setting": "Two students talk about a class project.",
            "speakers": [{"name": "Ana", "gender": "female"}, {"name": "Ben", "gender": "male"}], "lines": lines,
            "questions": [_mcq("What are they discussing?", "gist"), _mcq("What does Ana need?", "detail")]}


def ann_item(n: int | None = None) -> dict[str, Any]:
    n = n or next(_counter)
    body = "Please remember that the office will close early on Friday so finish your forms before noon and leave them at the front desk. "
    return {"topic": f"office {n}", "setting": "A staff member makes an announcement at the office.",
            "speaker": {"name": "Staff", "gender": "female"}, "text": f"Announcement {n}. {body * 2}".strip(),
            "questions": [_mcq("What is the purpose of the announcement?", "purpose"), _mcq("When will the office close?", "detail")]}


def talk_item(n: int | None = None) -> dict[str, Any]:
    n = n or next(_counter)
    body = "Plants need light and water to grow well, and scientists measure this process in many careful ways every single season. "
    return {"topic": f"plants {n}", "setting": "A professor gives a lecture in a biology class.",
            "speaker": {"name": "Professor", "gender": "male"}, "text": f"Lecture {n}. {body * 6}".strip(),
            "questions": [_mcq("What is the lecture mainly about?", "main_idea"), _mcq("What do plants need?", "detail"),
                          _mcq("What can be inferred?", "inference")]}


def rep_item(n: int | None = None) -> dict[str, Any]:
    n = n or next(_counter)
    name = "".join(chr(ord("a") + int(d)) for d in str(n))  # digits are rejected in spoken sentences
    return {"topic": f"topic {n}", "sentence": f"Student{name} " + "really " * (n % 5) + "reads books today."}


def interview_item(n: int | None = None) -> dict[str, Any]:
    n = n or next(_counter)
    return {"topic": f"topic {n}", "setting": f"An interviewer asks you about topic number {n}.",
            "interviewer": {"name": "Interviewer", "gender": "female"},
            "questions": [f"What do you like to do on day {n} of the week, question {k}?" for k in range(4)]}


def feedback(score: float = 4.0) -> dict[str, Any]:
    return {"score": score, "summary": "Good.", "strengths": ["Clear"],
            "errors": [{"category": "grammar", "quote": "x", "issue": "i", "fix": "f"}], "model_answer": "A model answer."}


def _count(prompt: str) -> int:
    return int(prompt.split("Create ")[1].split(" ")[0])


class RoutingFake(LLMProvider):
    """Answers by prompt type. Generation prompts yield fresh unique items; scoring prompts yield feedback."""

    name = "routing-fake"

    def __init__(self, score: float = 4.0, fail_generation: bool = False, fail_scoring: bool = False) -> None:
        self.score = score
        self.fail_generation = fail_generation
        self.fail_scoring = fail_scoring
        self.prompts: list[str] = []

    def complete(self, prompt: str, *, system: str | None = None, json_mode: bool = False, temperature: float = 0.8) -> str:
        from app.llm.errors import LLMError

        self.prompts.append(prompt)
        if "<transcript>" in prompt:
            if self.fail_scoring:
                raise LLMError("scoring down")
            n = prompt.count("RESPONSE ")
            return json.dumps({"items": [feedback(self.score) for _ in range(n)]})
        if "<student_response>" in prompt:
            if self.fail_scoring:
                raise LLMError("scoring down")
            return json.dumps(feedback(self.score))
        if self.fail_generation:
            raise LLMError("generation down")
        if 'Create ' in prompt and '"Build a Sentence"' in prompt:
            count = int(prompt.split("Create ")[1].split(" ")[0])
            return json.dumps({"items": [bas_item() for _ in range(count)]})
        if '"Listen and Repeat"' in prompt:
            return json.dumps({"items": [rep_item() for _ in range(_count(prompt))]})
        if '"Take an Interview"' in prompt:
            return json.dumps({"items": [interview_item() for _ in range(_count(prompt))]})
        if '"Listen and Choose a Response"' in prompt:
            return json.dumps({"items": [lcr_item() for _ in range(_count(prompt))]})
        if '"Listen to a Conversation"' in prompt:
            return json.dumps({"items": [conv_item() for _ in range(_count(prompt))]})
        if '"Listen to an Announcement"' in prompt:
            return json.dumps({"items": [ann_item() for _ in range(_count(prompt))]})
        if '"Listen to an Academic Talk"' in prompt:
            return json.dumps({"items": [talk_item() for _ in range(_count(prompt))]})
        if '"Complete the Words"' in prompt:
            return json.dumps({"items": [ctw_item() for _ in range(_count(prompt))]})
        if '"Read in Daily Life"' in prompt:
            return json.dumps({"items": [dl_item() for _ in range(_count(prompt))]})
        if '"Read an Academic Passage"' in prompt:
            return json.dumps({"items": [ap_item() for _ in range(_count(prompt))]})
        if '"Write an Email"' in prompt:
            return json.dumps({"items": [email_item()]})
        return json.dumps({"items": [discussion_item()]})


class FakeTTS:
    """Deterministic silent 'speech' whose length follows the text; records every synthesis call."""

    sample_rate = 22050

    def __init__(self, voices: list[str] | None = None) -> None:
        from app.audio.voices import VOICES

        self.voices = [v.name for v in VOICES] if voices is None else voices
        self.calls: list[tuple[str, str, float]] = []

    def available_voices(self) -> list[str]:
        return self.voices

    def synth(self, voice: str, text: str, length_scale: float) -> bytes:
        self.calls.append((voice, text, length_scale))
        return b"\x01\x00" * int(len(text) * 40 * length_scale)


class FakeStt:
    """Scripted transcriber: returns texts[file name] or a default; records calls."""

    def __init__(self) -> None:
        self.texts: dict[str, str] = {}
        self.default = "I really enjoy spending my free time with friends because we always have fun together and learn new things"
        self.calls: list[str] = []
        self.closed = 0
        self.fail = False

    def transcribe(self, path):
        from app.audio.stt import SttError, Transcript, Word

        self.calls.append(path.name)
        if self.fail:
            raise SttError("model exploded")
        text = self.texts.get(path.name, self.default)
        words = [Word(w, i * 0.4, i * 0.4 + 0.3, 0.9) for i, w in enumerate(text.split())]
        return Transcript(text=text, words=words, duration=len(words) * 0.4 + 1.0)

    def close(self) -> None:
        self.closed += 1
