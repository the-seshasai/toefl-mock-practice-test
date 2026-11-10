Create ${count} original "Listen to an Announcement" item(s) for a TOEFL-style listening test. Campus domain: ${domain}.

Each item is a spoken campus or classroom announcement by ONE speaker (a professor, an office staff member, a student-center host, a library or transport announcement) plus ${q_min}-${q_max} multiple-choice questions.

Fields:
- "topic": 2-4 words.
- "setting": one sentence shown on screen, e.g. "A professor makes an announcement at the start of class." (no spoilers).
- "speaker": {"name": "role or first name", "gender": "male" or "female"}.
- "text": the spoken announcement, ${word_min}-${word_max} words, natural spoken English with contractions; it should contain concrete details (dates, places, deadlines, conditions, reasons). No brackets, no stage directions, no markdown. Write numbers, dates and times in words.
- "questions": ${q_min}-${q_max} questions. Each: {"prompt": "...", "options": ["...", "...", "...", "..."], "answer": <index 0-3>, "kind": one of "main_idea", "purpose", "detail", "inference", "next_action", "explanation": "1-2 sentences"}.

Question rules: exactly one defensible answer; at least 2 different kinds. Vocabulary: ${vocabulary}. Depth: ${inference}. Distractors: ${distractors}. Never use "all/none of the above".

Do not reuse these recent announcements:
${avoid}

Original content only; never reproduce real test questions or copyrighted text.

Reply with ONLY JSON: {"items": [{"topic": "...", "setting": "...", "speaker": {"name": "...", "gender": "female"}, "text": "...", "questions": [{"prompt": "...", "options": ["...", "...", "...", "..."], "answer": 0, "kind": "detail", "explanation": "..."}]}]}
