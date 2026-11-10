Create ${count} original "Read in Daily Life" item(s) for a TOEFL-style reading test. Setting domain: ${domain}.

Each item is a short everyday text plus ${q_min}-${q_max} multiple-choice questions.

Fields:
- "topic": the specific situation (2-4 words).
- "format": the kind of text. Use these, one per item in order: ${formats}.
- "title": a short heading or subject line (may be "").
- "text": the text itself, ${word_min}-${word_max} words, formatted as it would really look (use line breaks "\n" for menus, schedules, emails, chats). Vocabulary: ${vocabulary}.
- "questions": ${q_min}-${q_max} questions. Each: {"prompt": "...", "options": ["...", "...", "...", "..."], "answer": <index 0-3 of the single correct option>, "kind": one of "main_purpose", "detail", "inference", "vocabulary", "reference", "explanation": "1-2 sentences saying why the answer is right and what makes a tempting distractor wrong"}.

Question rules:
- Exactly one option is correct and defensible from the text; the other three are clearly wrong.
- Use at least 2 different kinds across the questions. Depth: ${inference}. Distractors: ${distractors}.
- A "vocabulary" question must put the word being asked about in quotes, taken exactly from the text.
- Never use "all of the above", "none of the above" or "both A and B". Options should be similar in length.

Avoid these recent texts and do not repeat their situations:
${avoid}

Original content only; never reproduce real test questions or copyrighted text.

Reply with ONLY JSON: {"items": [{"topic": "...", "format": "...", "title": "...", "text": "...", "questions": [{"prompt": "...", "options": ["...", "...", "...", "..."], "answer": 0, "kind": "detail", "explanation": "..."}]}]}
