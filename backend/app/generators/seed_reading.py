"""Hand-written fallback items for Reading. Original content."""
from typing import Any

from app.spec import Difficulty, TaskType

B, I, A = Difficulty.BEGINNER, Difficulty.INTERMEDIATE, Difficulty.ADVANCED
CTW, DL, AP = TaskType.COMPLETE_THE_WORDS, TaskType.READ_DAILY_LIFE, TaskType.READ_ACADEMIC


def q(prompt: str, correct: str, wrong: list[str], kind: str, why: str) -> dict[str, Any]:
    return {"prompt": prompt, "options": [correct, *wrong], "answer": 0, "kind": kind, "explanation": why}


READING_SEEDS: list[tuple[TaskType, Difficulty, dict[str, Any]]] = [
    (CTW, B, {
        "topic": "walking for health",
        "text": "Many people enjoy walking in the park after work. Walking is a simple way to stay healthy because it needs no special "
                "equipment. A short walk every day can improve your mood and give you more energy. It also helps you sleep better at "
                "night. Many doctors suggest that adults walk for at least thirty minutes on most days.",
        "blanks": ["simple", "because", "special", "improve", "energy", "sleep", "night", "suggest", "thirty", "days"]}),
    (CTW, I, {
        "topic": "coral reefs",
        "text": "Coral reefs are among the most diverse ecosystems on Earth. They cover less than one percent of the ocean floor, yet they "
                "support about a quarter of all marine species. However, rising ocean temperatures cause corals to expel the algae that "
                "live inside them, which turns the reef white. Scientists call this process bleaching. If the water cools quickly, the "
                "coral can recover, but repeated heat waves often kill entire reefs. Protecting these habitats therefore requires "
                "reducing greenhouse gas emissions worldwide.",
        "blanks": ["cover", "support", "species", "cause", "algae", "turns", "process", "recover", "repeated", "requires"]}),
    (CTW, A, {
        "topic": "industrial time",
        "text": "The Industrial Revolution transformed not only how goods were produced but also how people understood time. Before "
                "factories, most workers followed the rhythms of daylight and the seasons. Mechanized production, by contrast, demanded "
                "strict schedules, so employers introduced clocks, bells and fines for lateness. Historians argue that this discipline "
                "gradually reshaped social habits well beyond the workplace. Even leisure became something that people measured, planned "
                "and, increasingly, purchased. Consequently, the modern notion of efficiency owes much to the demands of "
                "nineteenth-century industry.",
        "blanks": ["workers", "rhythms", "seasons", "demanded", "schedules", "employers", "discipline", "reshaped", "measured", "purchased"]}),
    (DL, B, {
        "topic": "library closing", "format": "a notice", "title": "Library Notice",
        "text": "The library will close at 6 p.m. on Friday, March 8, because of a staff meeting. Books can be returned in the box outside "
                "the main door. The library will open again at 9 a.m. on Saturday.",
        "questions": [
            q("Why will the library close early on Friday?", "There will be a staff meeting.",
              ["There is a book sale.", "The building needs repairs.", "It is a public holiday."], "detail",
              "The notice says the library closes 'because of a staff meeting'."),
            q("What should people do with books while the library is closed?", "Leave them in the box outside the door.",
              ["Bring them on Saturday only.", "Give them to a staff member at home.", "Keep them until March 8."], "detail",
              "Books can be returned in the box outside the main door."),
            q("What is the main purpose of this notice?", "To announce a change in opening hours",
              ["To advertise new books", "To ask for volunteers", "To explain library rules"], "main_purpose",
              "The notice mostly tells readers when the library closes and reopens.")]}),
    (DL, I, {
        "topic": "group project meeting", "format": "an email", "title": "Project meeting",
        "text": "Hi Jordan,\nI'm writing about the group project for Professor Hill's economics class. Our meeting has moved from Tuesday to "
                "Thursday at 4 p.m. because two members have lab sessions on Tuesday. We will meet in room 204 of the Business Building. "
                "Please bring your part of the data analysis, and let me know by Wednesday if Thursday does not work for you.\nThanks,\nMaya",
        "questions": [
            q("Why did Maya write this email?", "To change the time of a meeting",
              ["To cancel the project", "To ask for help with data analysis", "To report a lab result"], "main_purpose",
              "She tells Jordan the meeting moved from Tuesday to Thursday."),
            q("Where will the group meet?", "In room 204 of the Business Building",
              ["In Professor Hill's office", "In the library", "In a laboratory"], "detail",
              "The email names room 204 of the Business Building."),
            q("What should Jordan do if Thursday is a problem?", "Contact Maya by Wednesday",
              ["Come on Tuesday anyway", "Ask Professor Hill", "Skip the meeting"], "detail",
              "Maya asks to be told 'by Wednesday' if Thursday does not work.")]}),
    (DL, A, {
        "topic": "community workshops", "format": "an advertisement", "title": "Riverside Community Centre: Autumn Workshop Series",
        "text": "Our popular evening workshops return this October. Spaces are limited to twelve participants, and registration is on a "
                "first-come basis; late arrivals cannot be admitted once a session has begun because of safety rules in the studio.\n"
                "Mondays, 6:30 p.m.: Introduction to Pottery (materials included)\n"
                "Wednesdays, 7:00 p.m.: Beginner Photography (bring your own camera; loans are available on request)\n"
                "Saturdays, 10:00 a.m.: Family Cooking (children under ten must be accompanied)\n"
                "Fees are waived for residents over sixty-five. Anyone who cancels less than 48 hours in advance forfeits the fee unless "
                "the vacancy can be filled from the waiting list.",
        "questions": [
            q("Why are late arrivals not admitted to sessions?", "For safety reasons in the studio",
              ["Because spaces are limited to twelve", "To protect the cameras", "Because fees must be paid first"], "detail",
              "The notice cites 'safety rules in the studio'."),
            q("In the notice, the word 'forfeits' is closest in meaning to", "loses",
              ["earns", "borrows", "waits"], "vocabulary", "Someone who cancels late loses the fee they paid."),
            q("Who would NOT have to pay the fee for a Wednesday workshop?", "A resident who is seventy years old",
              ["A student who cancels early", "A child under ten", "A person with a camera"], "inference",
              "Fees are waived for residents over sixty-five, which includes a seventy-year-old resident.")]}),
    (AP, B, {
        "topic": "honeybees", "title": "Honeybees and Flowers",
        "passage": "Honeybees play an important role in producing the food we eat. When a bee visits a flower to collect nectar, grains of "
                   "pollen stick to its body. As the bee moves to the next flower, some of this pollen falls off, and the flower can then "
                   "produce seeds and fruit. This process is called pollination.\n\n"
                   "Farmers depend on bees for many crops, including apples, almonds, and blueberries. In recent years, however, the number "
                   "of honeybees has fallen in several countries. Scientists believe that chemicals used on farms, a loss of wild flowers, "
                   "and diseases all play a part. To help, some cities now plant flower gardens and ask people to avoid using strong "
                   "chemicals in their yards.",
        "questions": [
            q("What is the passage mainly about?", "How honeybees help produce food and why they are in danger",
              ["How farmers make honey", "Why flowers have bright colors", "How cities are built"], "main_idea",
              "Both paragraphs cover bees' role in food crops and the decline in their numbers."),
            q("What happens when pollen falls onto a flower?", "The flower can make seeds and fruit",
              ["The flower closes", "The bee stops working", "The flower turns brown"], "detail",
              "Paragraph 1 says the flower can then produce seeds and fruit."),
            q("In paragraph 1, the word 'nectar' is closest in meaning to", "a sweet liquid made by flowers",
              ["a kind of seed", "a type of insect", "a farm chemical"], "vocabulary", "Bees collect nectar from flowers; it is their sweet food."),
            q("Which of the following is NOT mentioned as a possible cause of fewer honeybees?", "Cold winters",
              ["Chemicals used on farms", "A loss of wild flowers", "Diseases"], "negative_detail",
              "Chemicals, fewer wild flowers and diseases are listed; winters are not."),
            q("What can be inferred about the cities mentioned in paragraph 2?", "They want to help bees survive",
              ["They sell honey", "They have no farms", "They ban all gardens"], "inference",
              "Planting flower gardens and limiting chemicals shows they are trying to protect bees.")]}),
    (AP, I, {
        "topic": "printing press", "title": "The Printing Press and Literacy",
        "passage": "Before the fifteenth century, books in Europe were copied by hand, usually by monks working slowly in monasteries. A "
                   "single volume could take months to finish, so books were expensive, and only wealthy individuals and religious "
                   "institutions could afford them. Literacy, as a result, remained limited to a small portion of the population.\n\n"
                   "Around 1450, Johannes Gutenberg developed a printing system that used movable metal type. Instead of carving an entire "
                   "page, printers arranged individual letters, inked them, and pressed them onto paper. The same letters could then be "
                   "rearranged and reused for the next page. This innovation dramatically reduced both the time and the cost of producing "
                   "books.\n\n"
                   "The consequences were profound. Within fifty years, millions of printed volumes had circulated across Europe, and ideas "
                   "travelled faster than ever before. Scholars could compare texts, merchants could keep standardized records, and "
                   "ordinary readers gained access to information that had once been guarded by institutions. Some historians therefore "
                   "regard the printing press as a decisive factor in the spread of education.",
        "questions": [
            q("What is the main idea of the passage?", "Movable type made books cheaper and helped spread knowledge",
              ["Monks were the best copyists in Europe", "Gutenberg was a wealthy merchant", "Paper was invented in the fifteenth century"],
              "main_idea", "The passage explains how printing lowered costs and widened access to information."),
            q("According to paragraph 1, why were books expensive before printing?", "Each one took months to copy by hand",
              ["Paper was rare", "Monks refused to sell them", "Taxes were high"], "detail",
              "A single volume could take months to finish, which made books costly."),
            q("In paragraph 2, the word 'movable' is closest in meaning to", "able to be rearranged",
              ["very heavy", "made of gold", "hard to find"], "vocabulary", "The letters were rearranged and reused for each page."),
            q("What can be inferred about literacy before the printing press?", "It was uncommon among ordinary people",
              ["It was higher than today", "It was taught in every home", "It was banned"], "inference",
              "Books were limited to the wealthy, so literacy stayed limited to a small portion of people."),
            q("Why does the author mention merchants and scholars in paragraph 3?", "To show different groups that benefited from printing",
              ["To criticize their habits", "To explain how books were copied", "To compare their wealth"], "rhetorical_purpose",
              "They are examples of groups who gained from wider access to printed material."),
            q("Which of the following is NOT stated as a result of the printing press?", "Books became harder to obtain",
              ["Ideas spread faster", "Printed volumes circulated widely", "Readers gained access to information"], "negative_detail",
              "Printing made books easier, not harder, to obtain.")]}),
]
