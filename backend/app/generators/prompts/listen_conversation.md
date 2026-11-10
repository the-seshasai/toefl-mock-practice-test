Create ${count} original "Listen to a Conversation" item(s) for a TOEFL-style listening test. Campus/social domain: ${domain}.

Each item is a short conversation between exactly two people (for example two students, a student and a professor, or a student and a staff member) plus ${q_min}-${q_max} multiple-choice questions. Only the audio is heard; the setting line is shown on screen.

Fields:
- "topic": 2-4 words.
- "setting": one sentence shown to the test taker, e.g. "A student talks to an advisor about changing her class schedule." (no spoilers).
- "speakers": exactly two: {"name": "short first name or role", "gender": "male" or "female"}. Use one of each gender when natural.
- "lines": the dialogue in order, 6-14 lines, each {"speaker": 0 or 1, "text": "..."}; speaker 0 starts and each speaker talks at least twice. Total ${word_min}-${word_max} words. Natural spoken English with contractions and a few discourse markers; no brackets, no stage directions, no markdown. Write numbers and times in words.
- "questions": ${q_min}-${q_max} questions. Each: {"prompt": "...", "options": ["...", "...", "...", "..."], "answer": <index 0-3>, "kind": one of "gist", "purpose", "detail", "inference", "attitude", "next_action", "explanation": "1-2 sentences"}.

Question rules: exactly one defensible answer; use at least 2 different kinds. Vocabulary: ${vocabulary}. Depth: ${inference}. Distractors: ${distractors}. Never use "all/none of the above".

Do not reuse these recent conversations:
${avoid}

Original content only; never reproduce real test questions or copyrighted text.

Reply with ONLY JSON: {"items": [{"topic": "...", "setting": "...", "speakers": [{"name": "...", "gender": "female"}, {"name": "...", "gender": "male"}], "lines": [{"speaker": 0, "text": "..."}], "questions": [{"prompt": "...", "options": ["...", "...", "...", "..."], "answer": 0, "kind": "detail", "explanation": "..."}]}]}
