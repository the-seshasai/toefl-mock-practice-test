Create ${count} original "Take an Interview" set(s) for a TOEFL-style speaking test. Topic domain: ${domain}.

An interviewer asks ONE test taker four spoken questions about a single topic. Each answer is spoken for about 45 seconds. The questions must get progressively harder: (1) a brief factual or personal question, (2) a question asking for a description or preference with a reason, (3) a question asking for an explanation or opinion, (4) a question asking for a prediction, comparison or hypothetical.

Fields:
- "topic": 2-4 words.
- "setting": one sentence shown on screen, e.g. "An interviewer asks you about how students use technology for learning." (no spoilers).
- "interviewer": {"name": "Interviewer", "gender": "male" or "female"}.
- "questions": exactly four strings, each ${word_min}-${word_max} words, natural spoken English, no brackets, no markdown, no digits (write numbers as words). Vocabulary: ${vocabulary}. Depth: ${depth}. At least three of them must be real questions ending in "?".

Do not reuse these recent interview topics:
${avoid}

Original content only; never reproduce real test questions or copyrighted text.

Reply with ONLY JSON: {"items": [{"topic": "...", "setting": "...", "interviewer": {"name": "Interviewer", "gender": "female"}, "questions": ["...", "...", "...", "..."]}]}
