Create ${count} original "Write an Email" prompt for a TOEFL-style writing test. Content domain: ${domain}.

The prompt describes a realistic academic or campus situation and asks the test taker to write an email.

Fields:
- "topic": the specific situation (2-5 words).
- "scenario": ${scenario_min}-${scenario_max} words. Describe who the writer is, the situation, and the recipient, then tell them to write an email. Written in second person ("You ...").
- "recipient": who receives the email (e.g. "Professor Alvarez, your biology instructor").
- "points": ${points_min}-${points_max} short imperative items the email must address (e.g. "Explain why you missed the deadline").

Difficulty requirements (strict): register - ${register}. Vocabulary - ${vocabulary}.
Avoid these recent scenarios and do not repeat their situations:
${avoid}

Original content only; never reproduce real test questions or copyrighted text.

Reply with ONLY JSON: {"items": [{"topic": "...", "scenario": "...", "recipient": "...", "points": ["...", "..."]}]}
