# CLAUDE.md — TOEFL iBT (2026 format) Practice App

## What this project is
A local, single-user web app for practicing the **redesigned TOEFL iBT (effective Jan 21, 2026)**.
It simulates all four sections in the official order, with official-style task types, timing, and
1–6 band scoring. Every attempt uses freshly generated questions. The user picks a difficulty level
before each exam. It runs on the user's own laptop; there are no accounts and no deployment target.

## Environment constraints (respect these)
- Dev machine: Ubuntu, 8 GB RAM, **no GPU**. Everything local must run on CPU.
- **Port 8000 is taken.** Backend runs on **8001**, frontend dev server on **5173**.
- LLM access: default provider is **Gemini** (`gemini-flash-lite-latest`, free tier, rate limited).
  OpenAI quota is exhausted, so do not use it. Claude API is an optional provider.
  All LLM calls go through one provider interface so the provider is swappable via `.env`.
- Never hardcode API keys. Read from `.env`; keep `.env.example` up to date.

## Tech stack
- Backend: Python 3.11+, FastAPI, SQLAlchemy + SQLite, Pydantic v2, pytest
- Frontend: React + Vite + TypeScript + Tailwind CSS
- Listening audio: local TTS (Piper) on CPU; cache generated audio on disk
- Speaking transcription: `faster-whisper` (`base` or `small`, int8, CPU); audio recorded in browser via MediaRecorder
- Package management: `uv` or `pip` + venv for backend, `npm` for frontend

## Repository layout
```
toefl-app/
  CLAUDE.md
  docs/FORMAT_SPEC.md        # single source of truth for exam structure (see below)
  backend/
    app/
      main.py
      config.py              # reads .env, ports, model names
      db.py, models.py, schemas.py
      llm/                   # provider interface + gemini.py (+ claude.py optional)
      generators/            # one module per task type
      validators/            # one validator per task type
      scoring/               # rubric scoring + band conversion
      audio/                 # tts.py, stt.py, cache
      routers/               # exams, sections, attempts, history
    tests/
  frontend/
    src/
      pages/                 # Setup, ExamRunner, Results, History
      sections/              # Reading/, Listening/, Writing/, Speaking/
      components/            # Timer, Recorder, AudioPlayer, WordCountless editors etc.
  data/                      # sqlite db, audio cache (gitignored)
```

## The format spec is law
`docs/FORMAT_SPEC.md` defines section order, task types, item counts, and timings. Code must read
these from config constants derived from that file, never scatter magic numbers. Summary:

- Order: **Reading → Listening → Writing → Speaking**. No break in a full exam.
- Reading (~27–30 min, adaptive): Complete the Words, Read in Daily Life, Read an Academic Passage
- Listening (~27–29 min, adaptive): Listen and Choose a Response, Conversation, Announcement, Academic Talk
- Writing (~23 min, 12 items, linear): Build a Sentence, Write an Email, Write for an Academic Discussion
- Speaking (~8 min, linear): Listen and Repeat, Take an Interview
- Section score: **1–6 bands in 0.5 steps**; total = average of the four section bands.
- Reading and Listening are **multistage adaptive** (router module, then easier or harder module).
  The app's difficulty selector sets the starting level; adaptive routing then runs on top of it.

If official ETS practice material contradicts `FORMAT_SPEC.md`, update the spec first, then the code.

## Core rules for question generation
1. **Never repeat.** Store a content hash (and topic + task type) of every generated item. Before
   serving, check against history; regenerate on collision. Vary topic domains and sentence patterns.
2. **Difficulty levels:** Beginner (band ~2–3), Intermediate (~3.5–4.5), Advanced (~5–6). Difficulty
   controls vocabulary level, passage length, distractor quality, speech rate, and inference depth.
   Encode this in a per-task difficulty table, not in ad-hoc prompt wording.
3. **Generate, then validate.** LLM output is structured JSON validated by Pydantic plus a
   task-specific validator (e.g., exactly one correct option, word counts in range, Complete the Words
   blanks are valid word fragments, Build a Sentence has one defensible ordering). Retry up to 3 times,
   then fall back to a cached item from the pre-generated bank.
4. **Pre-generate in the background** per exam so the user is never waiting mid-section.
   Respect Gemini rate limits: queue, backoff, and cache.
5. **No real ETS content.** Generate original items only; never reproduce copyrighted test material.

## Exam-runner behavior
- Timers are per-task/section and enforced client- and server-side; time expiry auto-submits.
- No going back after a section ends. Within a section, follow the real test's navigation rules.
- Setup screen: choose mode (Full test or single section or single task type), difficulty, and
  whether audio plays once (real) or replayable (practice).
- Listening audio plays **once** in exam mode, as on the real test.
- Speaking: show prep/record countdowns, record via mic, transcribe locally, then score.
- Autosave answers every few seconds so a refresh does not lose work.

## Scoring and feedback
- Reading/Listening: objective scoring, mapped to 1–6 bands using difficulty-weighted correctness.
- Writing/Speaking: LLM rubric scoring with a fixed rubric per task type, returned as JSON
  (score 0–5 mapped to bands, plus strengths, errors, and a rewritten model answer). Keep the
  rubric prompts in `backend/app/scoring/rubrics/` as versioned text files.
- Always label scores as **estimates**, not official ETS scores.
- Results page: section bands, per-task breakdown, review of every question with explanations,
  and a history chart of progress over time.

## Coding conventions
- Type hints everywhere in Python; strict TypeScript on the frontend.
- Small modules; one generator + one validator + one test file per task type.
- LLM prompts live in `backend/app/generators/prompts/*.md`, not inline in code.
- Every generator has a test using a mocked LLM (no network in tests).
- Run before finishing any task: `pytest -q` in backend, `npm run lint && npm run build` in frontend.
- Commit small and often with clear messages. Do not commit `.env`, `data/`, or audio cache.

## How to work in this repo
- Build incrementally in this order: scaffold, DB + config, LLM provider, one section end-to-end
  (Writing first), then the other sections, then adaptive routing, then history/analytics.
- After each milestone, run the app and verify it manually; report what you ran and what you saw.
- Ask before adding heavy dependencies; the machine has 8 GB RAM and no GPU.
- If something in the spec is ambiguous, pick the most faithful-to-real-TOEFL option, note it in
  `docs/DECISIONS.md`, and continue.
