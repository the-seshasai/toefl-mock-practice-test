# TOEFL iBT Practice (2026 format)

A local, single-user web app for practicing the **redesigned TOEFL iBT (effective January 2026)**.
It runs all four sections in the official order (Reading → Listening → Writing → Speaking) with the official task
types, timing and 1–6 band scoring. **Every attempt uses newly generated questions**, you choose the difficulty
before each exam, and everything runs on your own laptop: no accounts, no cloud deployment, no GPU.

> **These scores are estimates.** This is an independent practice tool, not affiliated with ETS. Bands are
> calculated by this app and are not official TOEFL scores. All questions are generated; none are real ETS content.

## What you get

- **Full test**, **one section**, or **one task type**, at **Beginner / Intermediate / Advanced**, in **Exam** mode
  (strict server-enforced timers, audio plays once) or **Practice** mode (timers optional, replay and re-record allowed).
- **Reading and Listening are two-stage adaptive**: Module 1 at your chosen level, then an easier or harder Module 2
  depending on how you did.
- **Writing**: Build a Sentence, Write an Email, Write for an Academic Discussion, scored against versioned rubrics.
- **Speaking**: Listen and Repeat and Take an Interview. You record in the browser; your speech is transcribed locally
  (Whisper) and scored.
- **Results** with a band per section, a per-task breakdown, every question reviewed with explanations, your own text
  or transcript next to a model answer, and playback of your recordings.
- **History** with score trends, your **weakest task types**, and a **"Practice my weak spots"** button.

## Requirements

| | |
|---|---|
| OS | Ubuntu 22.04 or newer (other Linux distributions should work) |
| Hardware | 8 GB RAM, CPU only, about 1 GB of free disk for models and caches |
| Python | 3.11 or newer, with [`uv`](https://docs.astral.sh/uv/) |
| Node.js | 20 or newer (with `npm`) |
| LLM | [Claude Code](https://claude.com/claude-code) installed and logged in (`claude` on your `PATH`) |
| Browser | Chrome, Chromium or Firefox with a microphone (for Speaking) |

The app has **no API keys**. All question generation and writing/speaking scoring runs through your own Claude Code
login (`claude -p`), so it counts against your Claude Code plan's usage. A full test makes dozens of short calls
(generation, plus scoring for Writing and Speaking); `CLAUDE_MODEL=haiku` keeps that light.

## Quick start

```bash
git clone <this repository> toefl-practice && cd toefl-practice
scripts/setup.sh        # checks tools, installs dependencies, creates .env, downloads the speech models
scripts/run_dev.sh      # starts the backend (8001) and the frontend (5173)
```

Then open **http://localhost:5173**. Open it as `localhost`, not by IP address: browsers only allow microphone access
on secure origins, and `localhost` counts as one.

The first exam takes one to a few minutes to prepare while questions are generated; later sections of a full test
are prepared in the background while you work.

## Manual setup

If you prefer to run the steps yourself (this is what `scripts/setup.sh` does):

```bash
# 1. Backend dependencies (creates backend/.venv)
cd backend && uv sync && cd ..

# 2. Frontend dependencies
cd frontend && npm ci && cd ..

# 3. Configuration
cp .env.example .env            # defaults work; see "Configuration" below

# 4. Claude Code login (once)
claude                          # follow the prompts, then exit

# 5. Speech models (about 400 MB, verified by checksum)
scripts/download_models.sh      # or --minimal, --voices, --whisper

# 6. Run
cd backend  && uv run uvicorn app.main:app --port 8001     # terminal 1
cd frontend && npm run dev                                 # terminal 2
```

### Speech models

`scripts/download_models.sh` is idempotent: it verifies SHA-256 checksums, skips files that are already correct,
and resumes interrupted downloads. If you would rather download by hand, put these files in place:

| Purpose | Files | Size | Source | Goes in |
|---|---|---|---|---|
| Listening and Speaking voices (Piper) | `en_US-ryan-medium`, `en_US-amy-medium`, `en_GB-alba-medium`, `en_GB-northern_english_male-medium` (each `.onnx` and `.onnx.json`) | 63 MB each | [`huggingface.co/rhasspy/piper-voices`](https://huggingface.co/rhasspy/piper-voices) under `en/<locale>/<name>/medium/` | `data/piper/` |
| Transcription (faster-whisper) | `model.bin`, `config.json`, `tokenizer.json`, `vocabulary.txt` | 145 MB total | [`huggingface.co/Systran/faster-whisper-base.en`](https://huggingface.co/Systran/faster-whisper-base.en) | `data/whisper/base.en/` |

- `scripts/download_models.sh --minimal` fetches only the two US voices (about 126 MB). Conversations then use the
  same two voices for everyone, and the UK accent is missing.
- Piper has no Australian English voice, so accents are US and UK only.
- To use a different Whisper model, download its files into `data/whisper/<name>/` and set `WHISPER_MODEL=<name>` in
  `.env`. `small.en` is more accurate on accented speech but needs about 1 GB of RAM and is roughly 3x slower;
  with 8 GB total, `base.en` is the safe choice.

## Configuration

Settings come from environment variables or a `.env` file **at the repository root** (copy `.env.example`).

| Variable | Default | Meaning |
|---|---|---|
| `CLAUDE_PATH` | `claude` | Path to the Claude Code executable |
| `CLAUDE_MODEL` | *(empty)* | `haiku` is fastest and lightest on your usage; `sonnet` is stronger; empty uses Claude Code's default |
| `LLM_MIN_INTERVAL_SECONDS` | `0` | Minimum spacing between LLM calls |
| `LLM_MAX_RETRIES` | `2` | Retries per failed call |
| `LLM_TIMEOUT_SECONDS` | `120` | Timeout per call |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | Allowed browser origin (CORS) |
| `DATA_DIR` | `<repo>/data` | SQLite database, generated audio, your recordings |
| `WHISPER_MODEL` | `base.en` | Model folder name under `WHISPER_DIR` |
| `WHISPER_DIR` | `<repo>/data/whisper` | Whisper models |
| `PIPER_VOICE_DIR` | `<repo>/data/piper` | Piper voices |

The ports are fixed on purpose: the backend uses **8001** (port 8000 is reserved on the development machine) and the
frontend dev server uses **5173**, which proxies `/api` to the backend.

## Using the app

1. **Setup page.** Choose *Full test*, *One section* or *One task type*, a difficulty, and a mode.
   - **Difficulty** sets the starting level (Beginner ≈ band 2–3, Intermediate ≈ 3.5–4.5, Advanced ≈ 5–6).
     Difficulty controls vocabulary, passage length, distractor quality, speech rate and inference depth.
   - **Exam** mode: timers are enforced by the server, audio plays once, one attempt per speaking response, no
     spellcheck. **Practice** mode: timers optional, audio can be replayed, you can re-record and play back.
2. **Preparing.** Questions are generated, checked and de-duplicated, and audio is synthesized.
3. **Take the exam.** Each task has its own clock. When it ends you move on automatically, and you cannot return to
   a finished task, module or section. Answers autosave every couple of seconds, so a refresh does not lose work.
   For Speaking, the start screen checks your microphone first.
4. **Results.** Estimated bands, the review of every item, and a link to your history.
5. **History.** Trend chart, a table of attempts, your weakest task types (adjusted for difficulty level), the
   most common writing and speaking error types, and **Practice my weak spots**, which builds a session from the
   task types you are weakest at.

### The adaptive sections

Reading and Listening have two modules. Module 1 runs at the level you chose. If you score **60% or more** on it,
Module 2 is one level harder; otherwise one level easier (clamped at Beginner and Advanced). Reading is 21 + 9
minutes; Listening is 18 + 7 (easier) or 18 + 11 (harder) minutes. Both possible Module 2s are prepared while you
take Module 1, so there is normally no wait. ETS does not publish its routing rules, so this threshold is a
transparent estimate.

### How bands are estimated

- **Reading and Listening:** objective scoring. Each module's fraction correct is mapped into a band range that
  depends on its level, and the modules are combined by point weight. Reaching a harder module never costs you.
- **Writing:** Build a Sentence is machine scored; Email and Academic Discussion are scored 0–5 by Claude against the
  rubrics in `backend/app/scoring/rubrics/` (versioned text files), with strengths, errors and a model answer.
- **Speaking:** *Listen and Repeat* is scored by code: your Whisper transcript is aligned to the target sentence and
  the match percentage maps to a 0–5 score (thresholds in `speaking_repeat.v1.txt`); missing, extra and changed words
  are listed. *Take an Interview* is scored 0–5 per answer by Claude from the transcript plus delivery statistics
  (speech rate, pauses, recognizer confidence).
- The overall score of a full test is the average of the four section bands, rounded to the nearest half band.

Speech recognition is imperfect: a word Whisper mishears can cost a point in Listen and Repeat.
The reasoning behind every modeling choice is in [`docs/DECISIONS.md`](docs/DECISIONS.md).

### How questions are generated

Each task type has a generator, a prompt (`backend/app/generators/prompts/*.md`) and a validator. The LLM returns
JSON; each item is checked (exactly one correct option, word counts, valid Complete-the-Words blanks, one defensible
Build-a-Sentence order, readability range per level) and a content hash is stored so **no item is ever served twice**.
Failed items are regenerated; if generation keeps failing, a small hand-written fallback bank keeps the exam going
(you will see a note on the start screen). Difficulty lives in one table per task (`backend/app/difficulty.py`).

## Data and privacy

Everything stays on your machine. Under `data/` (git-ignored):

| Path | Contents |
|---|---|
| `data/toefl.db` | Attempts, answers, scores, generated items |
| `data/audio/` | Generated Listening/Speaking prompt audio (tens of MB per full test; safe to delete) |
| `data/recordings/` | Your Speaking recordings |
| `data/piper/`, `data/whisper/` | Speech models |

To start from scratch without re-downloading models, delete `data/toefl.db*`, `data/audio` and `data/recordings`
(with the servers stopped). The database upgrades itself in place when new versions add columns.

## Performance on an 8 GB laptop

Measured on the development machine (8 GB RAM, 8 CPU threads, no GPU), with the desktop, a browser and other apps
already using about 6.5 GB:

- A complete scripted full test (all four sections, real LLM, real Piper, real Whisper) ran start to finish in about
  5 minutes and raised total system memory use to a peak of about 7.2 GB of 7.7 GB. The backend process itself held
  about 450 MB afterwards. It works, but there is little headroom: **close heavy applications before a full test.**
- Speech: Piper synthesizes at about 0.05x real time, and Whisper `base.en` transcribes at about 0.1x real time
  (a 5 s answer in about 0.5 s). Only one voice model is held in memory at a time, and Whisper is unloaded after each
  scoring job.
- Question generation is the slowest step: roughly 20 s (Speaking) to 1-2 minutes (Reading, Listening) for a fresh
  section, less when the item bank already holds unused items from earlier generation. Scoring a Speaking section takes
  about 30 s.
- Tasks are generated at most three at a time, because every LLM call is its own `claude` process.
- Free memory for generation: use `CLAUDE_MODEL=haiku`, and avoid `small.en` unless you have spare RAM.

## Troubleshooting

- **"Preparing your exam…" never finishes, or the section shows an error.** Run `claude -p "say hi"` in a terminal;
  if it fails, log in again with `claude`. The backend log (terminal running `run_dev.sh`) shows the reason for any
  generation failure. You may also have hit your Claude Code usage limit; wait and retry.
- **Listening or Speaking will not start ("Piper voices").** Run `scripts/download_models.sh`.
- **Speaking says the model is missing, or scoring fails.** Run `scripts/download_models.sh --whisper`. Failed scoring
  can be retried from the Results page.
- **The microphone prompt does not appear, or "Waiting for permission…" never ends.** Open the app at
  `http://localhost:5173` (not an IP address), click the lock icon in the address bar, allow the microphone, and press
  the button again.
- **The laptop becomes slow while generating.** Each LLM call is a separate process. Close memory-hungry apps, use
  `CLAUDE_MODEL=haiku`, and keep `small.en` for another day.
- **A port is in use.** `scripts/run_dev.sh` refuses to start if 8001 or 5173 is taken; stop the other program.
- **Audio will not play.** Browsers block audio until you interact with the page; press the Play button.
  In Exam mode a clip can be played once; reloading in the middle counts as played.

## Development

```bash
scripts/check.sh                      # ruff + pytest + frontend lint + build (run before finishing any change)
cd backend && uv run pytest -q        # tests only; no network, no models needed (two real-model tests skip themselves)
cd backend && uv run ruff check .
cd frontend && npm run lint && npm run build
```

- Tests use a scripted fake LLM, fake speech engines and a fake clock; the suite finishes in well under a minute.
- `python -m app.tools.difficulty_report --sample 2` (run in `backend/`, with `PYTHONPATH=.`) generates sample items at
  every level with the real LLM and reports their length and readability, for tuning `difficulty.py`.
- [`docs/FORMAT_SPEC.md`](docs/FORMAT_SPEC.md) is the single source of truth for exam structure (task types, item
  counts, timings), sourced from ETS's published blueprint; `backend/app/spec.py` holds the constants derived from it.
- [`docs/DECISIONS.md`](docs/DECISIONS.md) records every place the spec was ambiguous and what was chosen.
- Interactive API documentation is at http://localhost:8001/docs while the backend runs.

### Repository layout

```
scripts/                  setup.sh, download_models.sh, run_dev.sh, check.sh
docs/                     FORMAT_SPEC.md, DECISIONS.md
backend/app/
  main.py, config.py, db.py, models.py, schemas.py, spec.py, difficulty.py, runtime.py
  llm/                    provider interface + Claude Code provider
  generators/             one generator per task type, prompts/, fallback seed banks
  validators/             one validator per task type
  scoring/                bands, alignment, per-section scoring, rubrics/ (versioned text)
  audio/                  Piper TTS, faster-whisper STT, audio cache
  services/               exam engine (timers, adaptive routing), analytics
  routers/                attempts, history, analytics
  tools/                  difficulty report
backend/tests/            pytest suite
frontend/src/             pages/, sections/{Reading,Listening,Writing,Speaking}/, components/
data/                     database, audio, recordings, models (git-ignored)
```

## Known limitations

- Scores are estimates from a transparent model, not ETS's psychometric scoring.
- Accents are US and UK only (Piper has no Australian voice).
- Speech recognition errors can affect Listen and Repeat scores and the Interview transcript.
- Generated items vary in quality; each is validated, but a question may occasionally be ambiguous. The review page
  explains every answer, so you can judge.
- Refreshing in the middle of a recording loses that one recording (it uploads when it ends).
- Single user, single machine: there are no accounts and no deployment configuration.

## Credits

Speech synthesis by [Piper](https://github.com/OHF-Voice/piper1-gpl) and the voices in
[rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices); transcription by
[faster-whisper](https://github.com/SYSTRAN/faster-whisper) and the `faster-whisper-base.en` model. Please check the
license of each voice and model upstream before redistributing anything.

**Licensing note:** the `piper-tts` Python package is licensed **GPL-3.0-or-later** (faster-whisper is MIT). That is
fine for running this app on your own computer, but if you ever distribute this app together with Piper, the GPL's
terms apply to that distribution.
