Create ${count} original "Read an Academic Passage" item(s) for a TOEFL-style reading test. Academic domain: ${domain}.

Each item is a short university-style expository passage plus ${q_min}-${q_max} multiple-choice questions.

Fields:
- "topic": the specific subject (2-4 words).
- "title": a short passage title.
- "passage": ${word_min}-${word_max} words in at least 2 paragraphs separated by a blank line ("\n\n"). Informative, accurate, with a clear structure (for example cause and effect, comparison, a process or a debate). Vocabulary: ${vocabulary}. Readability: average sentence length about ${sentence_words} words and a Flesch-Kincaid grade level near ${fk_target} (never below ${fk_min} or above ${fk_max}); at low levels use short sentences and common words, at high levels longer sentences and abstract vocabulary.
- "questions": ${q_min}-${q_max} questions. Each: {"prompt": "...", "options": ["...", "...", "...", "..."], "answer": <index 0-3 of the single correct option>, "kind": one of "main_idea", "detail", "negative_detail", "inference", "vocabulary", "rhetorical_purpose", "reference", "explanation": "1-2 sentences saying why the answer is right and why the most tempting distractor is wrong"}.

Question rules:
- Include at least 3 different kinds, and always one "main_idea" and one "vocabulary" question.
- Exactly one option is correct and defensible from the passage. Depth: ${inference}. Distractors: ${distractors}.
- A "vocabulary" question must put the word in quotes, exactly as it appears in the passage ("In paragraph 1, the word 'X' is closest in meaning to").
- Never use "all of the above", "none of the above" or "both A and B". Options should be similar in length.
- Facts must be accurate general knowledge; do not invent studies or statistics attributed to real people.

Avoid these recent passages and do not repeat their topics:
${avoid}

Original content only; never reproduce real test questions or copyrighted text.

Reply with ONLY JSON: {"items": [{"topic": "...", "title": "...", "passage": "...", "questions": [{"prompt": "...", "options": ["...", "...", "...", "..."], "answer": 0, "kind": "main_idea", "explanation": "..."}]}]}
