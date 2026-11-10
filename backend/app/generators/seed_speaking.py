"""Hand-written fallback items for Speaking. Original content."""
from typing import Any

from app.spec import Difficulty, TaskType

B, I, A = Difficulty.BEGINNER, Difficulty.INTERMEDIATE, Difficulty.ADVANCED
LAR, INT = TaskType.LISTEN_AND_REPEAT, TaskType.TAKE_INTERVIEW


def rep(sentence: str) -> dict[str, Any]:
    return {"topic": "seed", "sentence": sentence}


def interview(topic: str, setting: str, gender: str, questions: list[str]) -> dict[str, Any]:
    return {"topic": topic, "setting": setting, "interviewer": {"name": "Interviewer", "gender": gender}, "questions": questions}


SPEAKING_SEEDS: list[tuple[TaskType, Difficulty, dict[str, Any]]] = [
    (LAR, B, rep("The bus leaves at seven thirty.")),
    (LAR, B, rep("Please open your book to page ten.")),
    (LAR, B, rep("My brother plays soccer every weekend.")),
    (LAR, B, rep("Where did you put my keys?")),
    (LAR, I, rep("The library will be closed on Monday because of the holiday.")),
    (LAR, I, rep("If you need help with your essay, visit the writing center.")),
    (LAR, I, rep("She decided to study abroad after she finished her degree.")),
    (LAR, I, rep("Students must return their laptops before the end of the semester.")),
    (LAR, A, rep("Although the experiment took longer than expected, the results were remarkably consistent.")),
    (LAR, A, rep("The committee, which had been meeting since early morning, finally reached a unanimous decision.")),
    (LAR, A, rep("Researchers who study migration patterns often rely on data collected over several decades.")),
    (INT, B, interview("free time", "An interviewer asks you about how you spend your free time.", "female", [
        "What do you like to do in your free time?",
        "Who do you usually spend your free time with?",
        "Do you prefer to be inside or outside on your days off? Why?",
        "What new activity would you like to try next year, and why?"])),
    (INT, I, interview("study habits", "An interviewer asks you about how you prepare for classes and exams.", "male", [
        "How do you usually prepare for an important exam?",
        "Describe a place on campus where you like to study and explain why.",
        "Some students prefer studying in groups, while others study alone. Which do you prefer, and why?",
        "How do you think technology will change the way students learn in the next ten years?"])),
    (INT, A, interview("city planning", "An interviewer asks you about what makes cities good places to live.", "female", [
        "What do you think is the most important factor in making a city enjoyable to live in?",
        "Describe a public space in your community and evaluate how well it serves local residents.",
        "Some cities restrict private cars in their centers. What are the advantages and disadvantages of such a policy?",
        "If you were responsible for a city's budget, how would you decide between funding public transport and building new housing?"])),
]
