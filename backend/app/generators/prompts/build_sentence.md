Create ${count} original "Build a Sentence" items for a TOEFL-style writing test. Content domain for this batch: ${domain}.

Each item has:
- "context": one short line (4-14 words) of dialogue or a question that the sentence naturally answers or continues.
- "correct_order": the target sentence split into ordered chunks (word groups) that a test taker will see shuffled.
- "acceptable_orders": other equally natural, fully grammatical orderings that use exactly the same chunks (almost always []).
- "explanation": 1-2 sentences naming the grammar point that fixes the order.
- "topic": the specific topic of the sentence (2-4 words).

Difficulty requirements (strict):
- The sentence has ${word_min}-${word_max} words total, split into ${chunk_min}-${chunk_max} chunks of 1-3 words each.
- Grammar level: ${grammar}. Vocabulary level: ${vocabulary}.
- Use these structures, one per item, in this order (cycle if needed): ${patterns}.
- Write the first chunk with a lowercase first letter unless it is "I" or a proper noun. Attach the final punctuation (. ? !) to the last chunk only.
- No two chunks may be identical. Choose chunk boundaries so exactly one ordering is natural: avoid free-floating adverbs or time phrases that could move; attach them to a neighboring chunk.
- Make each sentence about a different subject; do not reuse sentences from the avoid list below.
- Original content only. Never reproduce real test questions or copyrighted text.

Avoid these recent sentences:
${avoid}

Reply with ONLY JSON: {"items": [{"context": "...", "correct_order": ["...", "..."], "acceptable_orders": [], "explanation": "...", "topic": "..."}]}
