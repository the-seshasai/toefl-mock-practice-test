Create ${count} original sentences for a "Listen and Repeat" speaking task. Topic area for this batch: ${domain}.

A test taker hears each sentence once and must repeat it exactly, so each must be natural, meaningful spoken English that is easy to hold in memory and transcribe.

Requirements:
- Sentence lengths, one per item in this order: ${lengths}. Every sentence must be between ${word_min} and ${word_max} words.
- Vocabulary: ${vocabulary}. Structures: ${structures}.
- Each sentence is a plain statement or question about campus life, daily life or an academic topic. Vary the subjects and structures; do not start two sentences the same way.
- Write numbers and times as words ("seven thirty"), never digits. No brackets, no markdown, no quotation marks, no abbreviations that are read aloud ambiguously.
- End each sentence with . ? or !
- Do not reuse these recent sentences:
${avoid}

Original content only; never reproduce real test questions or copyrighted text.

Reply with ONLY JSON: {"items": [{"topic": "2-3 words", "sentence": "..."}]}
