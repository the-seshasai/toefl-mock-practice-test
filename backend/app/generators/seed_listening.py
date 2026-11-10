"""Hand-written fallback items for Listening. Original content; voices are assigned when the audio is built."""
from typing import Any

from app.spec import Difficulty, TaskType

B, I, A = Difficulty.BEGINNER, Difficulty.INTERMEDIATE, Difficulty.ADVANCED
LCR, CONV, ANN, TALK = (TaskType.LISTEN_CHOOSE_RESPONSE, TaskType.LISTEN_CONVERSATION,
                        TaskType.LISTEN_ANNOUNCEMENT, TaskType.LISTEN_ACADEMIC_TALK)


def q(prompt: str, correct: str, wrong: list[str], kind: str, why: str) -> dict[str, Any]:
    return {"prompt": prompt, "options": [correct, *wrong], "answer": 0, "kind": kind, "explanation": why}


def reply(topic: str, utterance: str, options: list[str], why: str) -> dict[str, Any]:
    return {"topic": topic, "utterance": utterance, "options": options, "answer": 0, "explanation": why}


def lines(*pairs: tuple[int, str]) -> list[dict[str, Any]]:
    return [{"speaker": s, "text": t} for s, t in pairs]


LISTENING_SEEDS: list[tuple[TaskType, Difficulty, dict[str, Any]]] = [
    (LCR, B, reply("offering water", "Would you like some water?",
                   ["Yes, please. I'm very thirsty.", "I walked to school.", "It is on the table.", "No, it was yesterday."],
                   "An offer is answered by accepting or refusing; the other replies do not respond to the offer.")),
    (LCR, B, reply("library hours", "What time does the library open?",
                   ["It opens at nine o'clock.", "Yes, I like books.", "It is very quiet.", "I went there last week."],
                   "The question asks for a time, and only the first reply gives one.")),
    (LCR, I, reply("asking for help", "I was wondering if you could help me carry these boxes.",
                   ["Sure, I'll grab the heavy ones.", "I don't have any boxes.", "They arrived in the mail yesterday.", "Yes, it was wonderful."],
                   "The speaker makes an indirect request; agreeing and offering help is the natural reply.")),
    (LCR, I, reply("course reading", "Did you finish the reading for tomorrow's seminar?",
                   ["Not yet, I'm only halfway through.", "The seminar is in room two.", "Yes, I read a book last year.", "I'll see you tomorrow morning."],
                   "A yes/no question about finishing the reading is answered by saying how far along you are.")),
    (LCR, A, reply("study group", "I'd love to join the study group, but I have a lab until seven.",
                   ["That's fine, we usually start around eight.", "Then I'll cancel the lab for you.", "Yes, the study group meets in the lab.",
                    "Seven is a good number for a group."],
                   "The speaker implies a scheduling conflict; the best reply solves it by pointing to a later start.")),
    (LCR, A, reply("late proposal", "Would it be a problem if I turned in the proposal a day late?",
                   ["Normally yes, but I can make an exception this once.", "The proposal was turned in yesterday by the group.",
                    "No, I haven't read the proposal yet today.", "A day is twenty-four hours long."],
                   "The speaker asks permission indirectly; the best reply grants or refuses it with a reason.")),
    (CONV, B, {
        "topic": "borrowing a book", "setting": "A student asks a librarian about borrowing a book.",
        "speakers": [{"name": "Maya", "gender": "female"}, {"name": "Mr. Lopez", "gender": "male"}],
        "lines": lines((0, "Hi, I'd like to borrow this book, please."), (1, "Sure. Do you have your student card?"), (0, "Yes, here it is."),
                       (1, "Thank you. You can keep the book for two weeks."), (0, "Two weeks? Can I keep it longer if I need to?"),
                       (1, "Yes, you can renew it online before the due date."), (0, "Great, thanks for your help.")),
        "questions": [
            q("Why does the student talk to the librarian?", "To borrow a book", ["To return a book", "To pay a fine", "To find a quiet room"], "purpose",
              "She says she would like to borrow a book."),
            q("How long can the student keep the book?", "Two weeks", ["Two days", "One month", "One week"], "detail", "The librarian says two weeks."),
            q("How can the student keep the book longer?", "By renewing it online", ["By paying a fee", "By asking a teacher", "By visiting every week"], "detail",
              "The librarian says she can renew it online before the due date.")]}),
    (CONV, I, {
        "topic": "presentation planning", "setting": "Two students talk about preparing for a presentation.",
        "speakers": [{"name": "Sam", "gender": "male"}, {"name": "Priya", "gender": "female"}],
        "lines": lines((0, "Hey Priya, have you started working on our biology presentation?"),
                       (1, "A little. I found some good articles about coral reefs, but I haven't made any slides yet."),
                       (0, "Same here. I've been busy with my part-time job, so I only have a rough outline."),
                       (1, "Well, we only have four days. Maybe we could meet tomorrow after class and divide the work."),
                       (0, "Tomorrow's tricky. I work until five. How about Thursday evening in the library?"),
                       (1, "That's a bit late, but okay. Let's each finish our slides by then, and we can practice together."),
                       (0, "Sounds like a plan. I'll send you my outline tonight.")),
        "questions": [
            q("What are the students mainly discussing?", "How to prepare for a group presentation",
              ["Which articles to read for a test", "Where to buy supplies for a project", "How to find a part-time job"], "gist",
              "They plan how to prepare and divide the work for their presentation."),
            q("Why can't Sam meet tomorrow after class?", "He has to work", ["He has a biology test", "He is traveling", "He is meeting a professor"], "detail",
              "Sam says he works until five."),
            q("What will Sam do tonight?", "Send Priya his outline", ["Finish all his slides", "Practice the presentation", "Book a library room"], "next_action",
              "He says he will send his outline tonight.")]}),
    (ANN, B, {
        "topic": "science fair", "setting": "A teacher makes an announcement at the end of class.",
        "speaker": {"name": "Ms. Green", "gender": "female"},
        "text": "Before you leave, I have a few reminders. The science fair is next Friday in the gym. Please bring your project to the gym by eight "
                "thirty in the morning. If your project needs electricity, tell me by Wednesday so I can arrange a table near a wall socket. "
                "Parents are welcome to visit at ten o'clock. Thank you, and have a good afternoon.",
        "questions": [
            q("What is the main purpose of the announcement?", "To remind students about the science fair",
              ["To cancel a class", "To explain a new grading rule", "To invite parents to dinner"], "purpose",
              "Almost every detail concerns preparing for the science fair."),
            q("What should students do if their project needs electricity?", "Tell the teacher by Wednesday",
              ["Bring a long cable", "Ask a parent for help", "Choose a different project"], "detail",
              "The teacher asks to be told by Wednesday so she can arrange a table near a socket.")]}),
    (ANN, I, {
        "topic": "library hours", "setting": "A university library announces changes to its opening hours.",
        "speaker": {"name": "Library announcement", "gender": "male"},
        "text": "Attention, students. Beginning next Monday, the main library will extend its weekday hours to help you prepare for final exams. "
                "The building will now stay open until two in the morning, instead of midnight. However, the quiet study floor on the fourth level "
                "will continue to close at midnight, because of staffing limits. Please note that the front desk will close at ten each evening, so "
                "any books you wish to borrow must be checked out before then. Self-service machines will remain available after ten for "
                "returning items. We hope these changes make your exam preparation easier. Thank you.",
        "questions": [
            q("Why is the library changing its hours?", "To help students prepare for final exams",
              ["To save electricity", "To reduce staff costs", "To repair the building"], "purpose", "The announcement says the extension is to help with final exams."),
            q("What will happen on the fourth floor at midnight?", "The quiet study floor will close",
              ["The front desk will open", "The self-service machines will stop", "The whole library will close"], "detail",
              "The quiet study floor keeps closing at midnight."),
            q("What can be inferred about borrowing books late in the evening?", "Students should borrow them before ten",
              ["Borrowing is possible at any time", "Only teachers may borrow", "Self-service machines lend books after ten"], "inference",
              "The front desk closes at ten, and the machines after ten are only for returns.")]}),
    (TALK, I, {
        "topic": "urban heat islands", "setting": "A professor gives a lecture in an environmental science class.",
        "speaker": {"name": "Professor", "gender": "female"},
        "text": "Today I want to talk about urban heat islands. If you've ever noticed that a city feels much hotter than the countryside around it, "
                "you've experienced this effect. So why does it happen? There are two main reasons. First, cities are full of dark surfaces, like "
                "asphalt roads and rooftops, which absorb sunlight and release it slowly as heat. Second, cities have fewer trees and less open soil, "
                "so there's less evaporation. Evaporation matters because it cools the air, much like sweating cools your body. Now, what can cities "
                "do about it? Some have started painting roofs white to reflect sunlight. Others are planting trees along streets and building small "
                "parks. One study of a large city found that neighborhoods with more trees were several degrees cooler on summer afternoons. The "
                "lesson is simple: how we design a city changes the weather people live in.",
        "questions": [
            q("What is the lecture mainly about?", "Why cities are hotter than nearby rural areas and how to cool them",
              ["How asphalt is made", "Why trees grow slowly in cities", "How sweating cools the body"], "main_idea",
              "The talk explains the causes of urban heat and some solutions."),
            q("According to the professor, why do dark surfaces make cities hotter?", "They absorb sunlight and release it as heat",
              ["They block the wind", "They create more clouds", "They hold water"], "detail", "Dark surfaces absorb sunlight and release it slowly as heat."),
            q("Why does the professor mention sweating?", "To explain how evaporation cools the air",
              ["To describe a health problem", "To compare two cities", "To introduce a new topic"], "organization",
              "Sweating is an analogy for evaporation cooling the air."),
            q("What can be inferred about neighborhoods with few trees?", "They are likely to be hotter in summer",
              ["They have more rain", "They are newer", "They have cleaner air"], "inference",
              "Trees cool neighborhoods, so areas without them should be warmer.")]}),
    (TALK, A, {
        "topic": "the spacing effect", "setting": "A professor lectures in a cognitive psychology course.",
        "speaker": {"name": "Professor", "gender": "male"},
        "text": "Let's turn to a phenomenon psychologists call the spacing effect, because it challenges a habit most of you probably rely on. "
                "Imagine two students preparing for the same exam. One studies for six hours the night before. The other studies for one hour a "
                "day over six days. Intuitively, many people assume the cramming student has an advantage, since the material is fresh. Yet "
                "decades of experiments suggest the opposite: the student who spaces the sessions retains far more a month later. Why? One "
                "explanation is that forgetting, paradoxically, helps. Each time you return to material after a delay, retrieving it requires "
                "effort, and that effort strengthens the memory trace. Cramming, by contrast, offers the illusion of mastery, because the "
                "information is still easy to recall, so you never practice the difficult retrieval that builds durable memory. Now, I'm not "
                "claiming that cramming never works. For a test tomorrow morning, it may be perfectly adequate. But if you need the knowledge "
                "next semester, or in your profession, spacing is clearly the better investment. The practical suggestion, then, is modest: "
                "distribute your study time, and let yourself forget a little between sessions.",
        "questions": [
            q("What is the main point of the lecture?", "Studying in spaced sessions leads to longer-lasting memory than cramming",
              ["Students should avoid studying the night before an exam", "Forgetting is a sign of poor intelligence", "Experiments on memory are unreliable"],
              "main_idea", "The whole talk contrasts spaced study with cramming and favors spacing."),
            q("According to the professor, why does spacing improve memory?", "Retrieving material after a delay strengthens the memory",
              ["It lets students sleep more", "It makes the material seem new", "It reduces the amount to study"], "detail",
              "Effortful retrieval after a delay strengthens the memory trace."),
            q("What is the professor's attitude toward cramming?", "It can be adequate for a short-term goal but is a poor long-term strategy",
              ["It is always harmful", "It is the best method", "It is irrelevant to exams"], "attitude",
              "He admits it may work for tomorrow's test but calls spacing the better investment."),
            q("What does the professor imply about the feeling of knowing material well after cramming?", "It can be misleading",
              ["It proves deep learning", "It lasts for months", "It only affects exams"], "inference",
              "He calls it an 'illusion of mastery'."),
            q("Why does the professor describe two students?", "To illustrate the contrast between two study strategies",
              ["To criticize a particular student", "To introduce a new experiment", "To explain grading"], "purpose",
              "The example sets up the comparison between cramming and spacing.")]}),
]
