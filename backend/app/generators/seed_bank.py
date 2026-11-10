"""Small hand-written fallback bank so a failed generation never blocks an exam. Original content."""
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.generators import REGISTRY
from app.generators.base import content_hash
from app.generators.seed_listening import LISTENING_SEEDS
from app.generators.seed_reading import READING_SEEDS
from app.generators.seed_speaking import SPEAKING_SEEDS
from app.models import Item
from app.spec import Difficulty, TaskType

B, I, A = Difficulty.BEGINNER, Difficulty.INTERMEDIATE, Difficulty.ADVANCED


def _bas(difficulty: Difficulty, context: str, order: list[str], explanation: str) -> tuple[TaskType, Difficulty, dict[str, Any]]:
    return TaskType.BUILD_A_SENTENCE, difficulty, {
        "context": context, "correct_order": order, "acceptable_orders": [], "explanation": explanation, "topic": "seed",
    }


SEEDS: list[tuple[TaskType, Difficulty, dict[str, Any]]] = [
    _bas(B, "What did you do after school yesterday?", ["I", "played soccer", "with my friends", "after school."],
         "English statements follow subject, verb, object, then the time phrase."),
    _bas(B, "Where is the library?", ["The library", "is next to", "the science", "building."],
         "'Is next to' introduces the location after the subject."),
    _bas(B, "Why are you wearing a coat?", ["Because", "it is", "very cold", "outside today."],
         "'Because' begins the clause that gives the reason."),
    _bas(B, "What is your sister doing?", ["She is", "reading a book", "in her", "room now."],
         "Present continuous: subject + is + verb-ing, then place and time."),
    _bas(I, "Did the professor say anything about the exam?", ["She said", "the exam", "will cover", "only the first", "three chapters."],
         "Reported speech keeps subject-verb order after 'said'."),
    _bas(I, "Why was Maria late for class?", ["Maria missed", "the bus", "because", "her alarm", "did not", "ring this morning."],
         "The reason clause with 'because' follows the main clause; 'did not' precedes the base verb."),
    _bas(I, "What are your plans for the weekend?", ["If the weather", "is nice,", "we will", "go hiking", "in the mountains."],
         "A first conditional puts the if-clause (present tense) before the 'will' clause."),
    _bas(I, "What does the museum offer on Sundays?", ["On Sundays,", "visitors can", "join a free", "guided tour", "of the", "new exhibit."],
         "A fronted time phrase takes a comma, then subject, modal, and base verb."),
    _bas(A, "How did the committee respond to the proposal?",
         ["The committee", "rejected", "the proposal", "that the students", "had submitted", "because it", "lacked", "a clear budget."],
         "The relative clause 'that the students had submitted' directly follows the noun it modifies."),
    _bas(A, "Do you think remote work will last?",
         ["Few people", "who have worked", "from home", "would willingly", "return to", "a full-time", "office schedule."],
         "The relative clause modifies 'people'; 'would willingly return' follows the subject phrase."),
    (TaskType.WRITE_EMAIL, B, {
        "topic": "missed class", "recipient": "Ms. Carter, your English teacher",
        "scenario": "You are a student at Lakeview College. You missed your English class yesterday because you were sick. "
                    "Write an email to your teacher, Ms. Carter. Explain why you were absent and ask what homework you missed.",
        "points": ["Explain why you missed class", "Ask about the homework you missed"]}),
    (TaskType.WRITE_EMAIL, I, {
        "topic": "damaged laptop", "recipient": "the library's equipment manager",
        "scenario": "You borrowed a laptop from your university's library for a group project, but the screen cracked while you were "
                    "carrying it to class. Write an email to the library's equipment manager. Describe what happened, apologize, "
                    "and ask what you need to do to resolve the situation.",
        "points": ["Describe what happened", "Apologize", "Ask how to resolve the situation"]}),
    (TaskType.WRITE_EMAIL, A, {
        "topic": "club budget cut", "recipient": "the dean of student affairs",
        "scenario": "You are the president of the university hiking club. The dean's office has announced that all student clubs must "
                    "reduce their budgets by thirty percent next semester, which would force your club to cancel its annual trip. "
                    "Write an email to the dean of student affairs. Explain the value of the trip to students, propose a compromise, "
                    "and request a short meeting to discuss it.",
        "points": ["Explain the value of the trip", "Propose a compromise", "Request a short meeting"]}),
    (TaskType.WRITE_ACADEMIC_DISCUSSION, B, {
        "topic": "school lunch", "professor_name": "Dr. Lee",
        "professor_post": "This week we are talking about healthy habits at school. Some schools sell only healthy food in their "
                          "cafeterias. Do you think schools should stop selling snacks and sweet drinks? Why or why not?",
        "students": [
            {"name": "Ana", "text": "I think schools should stop selling sweet drinks. Students drink too much sugar, and it is bad for their health."},
            {"name": "Ben", "text": "I disagree with Ana. Students should choose for themselves, and a small snack helps them stay awake during long classes."}]}),
    (TaskType.WRITE_ACADEMIC_DISCUSSION, I, {
        "topic": "online lectures", "professor_name": "Professor Reyes",
        "professor_post": "In our unit on education and technology, we have looked at the growth of recorded lectures. Many universities now "
                          "post every lecture online, and some students stop attending class in person. Should universities require "
                          "students to attend lectures in person, even when recordings are available? Explain your position.",
        "students": [
            {"name": "Priya", "text": "Attendance should be required. Live lectures let students ask questions and discuss ideas right away, "
                                     "and that kind of interaction is very hard to copy when you are watching a recording alone at home."},
            {"name": "Marcus", "text": "I would not require it. Recordings let students replay difficult parts as often as they need, and many of us "
                                      "work part-time, so a strict attendance rule would be unfair to students with busy schedules."}]}),
    (TaskType.WRITE_ACADEMIC_DISCUSSION, A, {
        "topic": "urban green space", "professor_name": "Dr. Nakamura",
        "professor_post": "Our readings this week examined how cities allocate limited land. Planners often face a choice between "
                          "preserving public parks and building affordable housing on the same sites. Because both goals serve "
                          "the public interest, and because each choice affects thousands of residents for decades, the trade-off is rarely simple. Which should receive priority when the two conflict, "
                          "and how should planners justify their decision to residents?",
        "students": [
            {"name": "Elena", "text": "Housing should take priority. A shortage of affordable homes pushes families out of the city and increases "
                                      "commuting and inequality, while a park, however valuable, can often be partly replaced by smaller green spaces nearby, so the overall loss to residents is smaller."},
            {"name": "Tomas", "text": "I would protect the parks. Green space improves public health and reduces urban heat, and these "
                                      "benefits are almost impossible to restore once land has been developed, whereas housing can be built elsewhere if planners are willing to look beyond protected land."}]}),
]

SEEDS.extend(READING_SEEDS)
SEEDS.extend(LISTENING_SEEDS)
SEEDS.extend(SPEAKING_SEEDS)


def ensure_seeded(db: Session) -> None:
    for task_type, difficulty, payload in SEEDS:
        gen = REGISTRY[task_type]
        parsed = gen.item_model.model_validate(payload)
        digest = content_hash(task_type, gen.content_key(parsed))
        if db.scalar(select(Item.id).where(Item.content_hash == digest)) is None:
            db.add(Item(task_type=task_type.value, difficulty=difficulty.value, topic="seed", content_hash=digest,
                        payload=gen.to_payload(parsed), served=False, source="seed"))
    db.commit()
