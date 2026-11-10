Create ${count} original "Listen and Choose a Response" items for a TOEFL-style listening test. Mix of everyday and campus situations; vary the domain, using ${domain} for several of them.

The test taker hears ONE short spoken line and must choose the best reply from four written options. The spoken line is never shown on screen.

Each item: {"topic": "2-4 words", "utterance": "...", "options": ["...", "...", "...", "..."], "answer": <index 0-3 of the single best reply>, "explanation": "1-2 sentences on why it is the best reply and why the most tempting wrong option fails"}.

Rules:
- The utterance is ${word_min}-${word_max} words, natural spoken English with contractions, suitable for text-to-speech: no brackets, no stage directions, no markdown. Write numbers and times in words ("nine thirty").
- Vary the speech act across items: a question, a request, an offer, an invitation, a complaint, a suggestion, a statement that needs a reaction.
- Options are short replies (3-14 words), all grammatical. Exactly one is a natural, appropriate reply. Distractors: ${distractors}. Vocabulary: ${vocabulary}.
- Never use "all of the above" or "none of the above".
- Do not reuse these recent lines:
${avoid}

Original content only; never reproduce real test questions or copyrighted text.

Reply with ONLY JSON: {"items": [{"topic": "...", "utterance": "...", "options": ["...", "...", "...", "..."], "answer": 0, "explanation": "..."}]}
