Create ${count} original "Listen to an Academic Talk" item(s) for a TOEFL-style listening test. Academic domain: ${domain}.

Each item is an excerpt of a university lecture by ONE speaker plus ${q_min}-${q_max} multiple-choice questions. Only the audio is heard.

Fields:
- "topic": 2-4 words.
- "setting": one sentence shown on screen, e.g. "A professor gives a lecture in an environmental science class." (no spoilers).
- "speaker": {"name": "Professor", "gender": "male" or "female"}.
- "text": the spoken lecture, ${word_min}-${word_max} words. Spoken style: contractions, rhetorical questions, signposting ("so", "now", "the key point is"), one clear example. Accurate general knowledge only; do not invent studies attributed to real people. No brackets, no stage directions, no markdown. Write numbers in words.
- "questions": ${q_min}-${q_max} questions. Each: {"prompt": "...", "options": ["...", "...", "...", "..."], "answer": <index 0-3>, "kind": one of "main_idea", "purpose", "detail", "inference", "organization", "attitude", "vocabulary", "explanation": "1-2 sentences"}.

Question rules: include at least 3 different kinds and always one "main_idea". Exactly one defensible answer. A "vocabulary" question quotes a word or phrase exactly as spoken. Vocabulary: ${vocabulary}. Depth: ${inference}. Distractors: ${distractors}. Never use "all/none of the above".

Do not reuse these recent talks:
${avoid}

Original content only; never reproduce real test questions or copyrighted text.

Reply with ONLY JSON: {"items": [{"topic": "...", "setting": "...", "speaker": {"name": "Professor", "gender": "female"}, "text": "...", "questions": [{"prompt": "...", "options": ["...", "...", "...", "..."], "answer": 0, "kind": "main_idea", "explanation": "..."}]}]}
