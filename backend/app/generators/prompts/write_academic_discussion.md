Create ${count} original "Write for an Academic Discussion" prompt for a TOEFL-style writing test. Content domain: ${domain}.

It shows an online class discussion: a professor poses a question, and two students have already posted different views.

Fields:
- "topic": the specific topic (2-5 words).
- "professor_name": e.g. "Dr. Okafor".
- "professor_post": ${prof_min}-${prof_max} words. Introduces the topic briefly and ends by asking a clear question the class must answer. Question type: ${stance}.
- "students": exactly two posts, each {"name": "...", "text": "..."} with ${student_min}-${student_max} words. They must take clearly DIFFERENT positions or emphasize different reasons, written in natural student voice. Use different first names.

Vocabulary level: ${vocabulary}.
Avoid these recent professor posts and do not repeat their topics:
${avoid}

Original content only; never reproduce real test questions or copyrighted text.

Reply with ONLY JSON: {"items": [{"topic": "...", "professor_name": "...", "professor_post": "...", "students": [{"name": "...", "text": "..."}, {"name": "...", "text": "..."}]}]}
