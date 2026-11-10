Create ${count} original "Complete the Words" paragraph(s) for a TOEFL-style reading test. Content domain: ${domain}.

The test taker will see the paragraph with the second half of ${blank_count} words hidden and must type the missing letters, so the context must make each hidden word predictable.

Each item has:
- "topic": the specific topic (2-4 words).
- "text": a coherent academic-style paragraph of ${word_min}-${word_max} words with at least 4 complete sentences. Vocabulary: ${vocabulary}.
- "blanks": exactly ${blank_count} words from the text, in the order they appear, to be partially hidden.

Rules for "blanks":
- Pick words that are strongly predictable from the surrounding sentence (for example verbs, nouns and adjectives completing a clear idea, and some function words like "because" or "although").
- Each is a single plain word of at least 3 letters (letters only: no hyphens, digits, apostrophes or capital-letter proper nouns), all different from each other.
- None may come from the first sentence (the first sentence stays fully visible).
- Never choose two neighboring words; leave at least one word between blanks.
- Each chosen word must appear in the text exactly as written in "blanks".

Avoid these recent paragraphs and do not repeat their topics:
${avoid}

Original content only; never reproduce real test questions or copyrighted text.

Reply with ONLY JSON: {"items": [{"topic": "...", "text": "...", "blanks": ["...", "..."]}]}
