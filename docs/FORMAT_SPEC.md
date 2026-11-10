# TOEFL iBT (2026 format) — Format Specification

Single source of truth for exam structure. Code reads these values from `backend/app/spec.py`
(constants derived from this file). If official material changes, update this file first.

**Sources (retrieved 2026-11-09)**
- ETS, *Test Content and Structure* — https://www.ets.org/toefl/test-takers/ibt/about/content.html
- ETS, *TOEFL iBT Test: 2026 Update — Test Blueprint and Specifications Document* (PDF) —
  https://www.ets.org/content/dam/ets-org/pdfs/toefl/toefl-ibt-test-specifications-2026.pdf
- ETS Help, *TOEFL iBT updates coming January 2026* — https://toeflaccess.ets.org/help/en/articles/11758550-toefl-ibt-updates-coming-january-2026

Anything marked **[ASSUMPTION]** is not stated by ETS; the choice is recorded in `DECISIONS.md`.

## Overview

| Section   | Task types                                                                                      | Items | Base time |
|-----------|--------------------------------------------------------------------------------------------------|------:|----------:|
| Reading   | Complete the Words · Read in Daily Life · Read an Academic Passage                              | 50    | ~30 min   |
| Listening | Listen and Choose a Response · Listen to a Conversation · Listen to an Announcement · Listen to an Academic Talk | 47 | ~29 min |
| Writing   | Build a Sentence · Write an Email · Write for an Academic Discussion                            | 12    | ~23 min   |
| Speaking  | Listen and Repeat · Take an Interview                                                           | 11    | ~8 min    |

- Official order: **Reading → Listening → Writing → Speaking**. No scheduled break.
- Times exclude directions. Whole test ≈ 1 h 23 min – 1 h 29 min (blueprint); ETS marketing says "about two hours" including directions/check-in.
- Reading and Listening are **two-stage adaptive** (router module → lower or upper module). Writing and Speaking are **linear**.
- No going back to a finished section. Notes on scratch paper allowed; writing-assistance software not allowed.
- Items counts include **unscored pretest items** in Reading (50 items → 35 raw points) and Listening (47 items → 35 raw points).

## Reading (~30 min, adaptive, 50 items, 35 scored points)

Structure: router module ≈ 30 items? **[AMBIGUOUS]** — blueprint lists "Items 30 + 20 = 50" and "18–21 min" for
router+module, "9 min" for the second stage. We model: **Router ≈ 9 min / ~25 items, then Lower or Upper module ≈ 9–21 min**,
and keep total at ≤ 50 items / ~30 min. **[ASSUMPTION]** see DECISIONS D-03.

| Task | Items | CEFR | Notes |
|------|------:|------|-------|
| Complete the Words | ~30 blanks total across the section (10 per paragraph, ~3 paragraphs) **[ASSUMPTION on split]** | B1–C1+ | Short academic paragraph; some words have missing trailing letters; test taker types the missing letters. Texts ≤ ~100 words. |
| Read in Daily Life | 5–15 items, in sets of **2 or 3** questions per text | A1–C1 | Short non-academic texts (sign, menu, email, social post, notice, schedule); 15–50 words easy up to ~150–200 words. |
| Read an Academic Passage | 5–15 items (≈ 5 per passage) | B1–C2 | Extended academic passage, up to ~200 words per spec text (ETS practice passages run longer); main idea, detail, inference, idea relationships, rhetorical structure, vocabulary-in-context. |

- Texts remain visible while answering. 1 point per scored item. Machine scored.
- Text complexity: medium ≈ FK grade 7.4–10.5, high ≈ 10.5–20 (used in our difficulty table).

## Listening (~29 min, adaptive, 47 items, 35 scored points)

Router ≈ 18 min; second stage Lower ≈ 7 min / Upper ≈ 11 min (blueprint).

| Task | Items | CEFR | Notes |
|------|------:|------|-------|
| Listen and Choose a Response | 15–19 | A1–B2 | One short utterance (≤ ~6 stressed syllables to one short sentence); choose the best reply. One item per audio. |
| Listen to a Conversation | 10 | A2–C1 | Two-speaker campus/social exchange (≈ 35–100 words); ~2–3 questions per conversation. |
| Listen to an Announcement | 6–10 | A2–C1 | Campus/class announcement (monologue); questions follow. |
| Listen to an Academic Talk | 8–16 | A2–C2 | Lecture excerpt up to ~250 words; main/supporting ideas, inference, idioms. |

- **Audio plays once** (exam mode). Speakers: balanced accents/gendered voices (US/Canadian, Australian, British).
- Printed stems + multiple choice, shown after audio. 1 point per scored item. Machine scored.

## Writing (~23 min, linear, 12 items, 20 raw points)

| Task | Items | Points | Notes |
|------|------:|-------:|-------|
| Build a Sentence | 10 | 1 each | Reorder given words/chunks into a grammatical sentence in response to a short context line. Machine scored. |
| Write an Email | 1 | 0–5 | Scenario; write a multi-sentence email with appropriate tone. AI scored. **[ASSUMPTION]** ~7 min, ~80–120+ words. |
| Write for an Academic Discussion | 1 | 0–5 | Professor question + two student posts; write a paragraph-length contribution. AI scored. Real task: ~10 min, ≥100 words. |

- Timing inside the 23 min: Build a Sentence ≈ 6 min total (≈ 35 s each, **[ASSUMPTION]**), Email ≈ 7 min, Discussion ≈ 10 min.
- Plain text editor; no writing-assistance software.

## Speaking (~8 min, linear, 11 items, 55 raw points)

| Task | Items | Points | Notes |
|------|------:|-------:|-------|
| Listen and Repeat | 7 | 0–5 each | Hear a sentence once, repeat it exactly; length/complexity increase across the 7 items (A1→C2). AI scored for accuracy and intelligibility. |
| Take an Interview | 4 | 0–5 each | Interviewer asks 4 questions on one topic; responses progress from brief factual to opinion/explanation/prediction. Per-question countdown (**[ASSUMPTION]** 45 s response; no prep time). AI scored. |

- Scenario introduced aurally and in print. Responses recorded; sentences use natural contractions.

## Scoring

- Each section reported on a **1–6 scale in 0.5 steps**, aligned to CEFR. Overall = **average of the four sections, rounded to the nearest half band** (5.125 → 5.0).
- ETS also reports a comparable 0–120 score during a 2-year transition after Jan 2026 (we do not emulate this).
- Reading/Listening: adaptive; difficulty of the second stage affects the band. We approximate with difficulty-weighted correctness. **[ASSUMPTION]** (ETS does not publish its IRT mapping.)
- Writing/Speaking: AI-scored 0–5 per constructed-response item. Writing section raw = 10 (BaS) + 5 + 5 = 20; Speaking raw = 11 × 5 = 55.
- **Every score in this app is an estimate, not an official ETS score.**

## CEFR ↔ band guide (used for the difficulty table)

| Band | CEFR approx. | App level |
|-----:|--------------|-----------|
| 1–2  | A1–A2 | Beginner (target band ~2–3) |
| 3–4  | B1–B2 | Intermediate (~3.5–4.5) |
| 5–6  | C1–C2 | Advanced (~5–6) |

## How this app implements the spec

The blueprint above is the contract; where ETS is silent the app chooses and records it in `DECISIONS.md`.

| Topic | Implementation |
|---|---|
| Two-stage adaptive Reading/Listening | Module 1 at the chosen level; Module 2 one level easier or harder if Module 1 scores below or at/above 60% (D-25) |
| Reading time | Module 1 21 min + Module 2 9 min = 30 min (blueprint: 18-21 min + 9 min) |
| Listening time | Module 1 18 min + Module 2 of 7 min (easier) or 11 min (harder), matching the blueprint |
| Scored points | Reading about 50 and Listening about 47-50 *scored* items; ETS's 35-point raw scores include unscored pretest items we do not model |
| Writing | 10 Build a Sentence + Email + Academic Discussion in 23 min (6 / 7 / 10 min per task, our split) |
| Speaking | 7 Listen and Repeat + 4 interview questions in 8 min (3 / 5 min per task, our split) |
| Section band | 1-6 in 0.5 steps; adaptive sections combine modules by point weight (D-26) |
| Overall band | Average of the four sections rounded to the nearest 0.5 (ETS wording) |
| Single-task / weak-spot sessions | Not adaptive: one stage, the usual set sizes and timers |
