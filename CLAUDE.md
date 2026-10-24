# CLAUDE.md — Kasauti

Kasauti is a verification layer inside a bank's app. It reads the claims in an investment ad or trading-app screenshot, tests each claim against a record the scammer cannot edit (depository holdings via Account Aggregator, SEBI/RBI registries, original official footage), and shows the mismatch as plain facts in Hindi or English, with a one-tap report path.

Hackathon: Amazon AI Cyber Security Hackathon, IIT Delhi, Track 03 (Deepfake Detection for Financial Communications). Team Alpha. 48-hour finale build.

Read PRD.md for requirements and progress.md for current state before starting any task.

## Orchestration (who does what)

| Role | Model | Effort | How it runs |
|---|---|---|---|
| Lead + main coding | Opus 5.5 (`claude-opus-5-5`) | high | The main session |
| Parallel module builds | Opus 5.5 | high | `module-builder` subagent, own git worktree |
| Reading context | Sonnet 5.5 (`claude-sonnet-5-5`) | high | `context-reader` subagent, read-only |
| Writing progress.md | Sonnet 5.5 | high | `progress-keeper` subagent, edits only progress.md |
| Small tasks | Haiku (latest) | high | `chore-runner` subagent; also the default for any unnamed subagent |

Routing rules for the lead:
1. Before touching unfamiliar code or data, send `context-reader` to brief you. Don't read large files into the main context yourself.
2. Write core logic yourself: schemas, verdict rules, evidence chain, integration. These are the parts judges will question.
3. Hand a self-contained module with a fixed interface to `module-builder` when it can run in parallel.
4. Send test runs, lint, fixture generation, data cleanup, boilerplate and renames to `chore-runner`.
5. After every finished task, decision or new blocker, call `progress-keeper` with a 2–5 line summary. Never skip this; teammates on other laptops rely on progress.md.
6. Wait for a subagent's result before building on it.

Effort is forced to high for every model by `CLAUDE_CODE_EFFORT_LEVEL` in `.claude/settings.json`.

## Non-negotiable rules

- **Rules decide, never the LLM.** The LLM only turns an artifact into claims in the fixed schema (`backend/app/schemas/claims.py`). Verdicts and user-facing text come from `backend/app/verdict/` and fixed templates.
- **Three outcomes only:** `MATCHES`, `CONTRADICTS`, `NO_RECORD`. Never output "safe", "verified", "genuine" or a percentage as a verdict. A detector score may appear only labelled "weak signal".
- **No false contradiction.** A holdings claim can be `CONTRADICTS` only if every depository in the consent scope was queried successfully. Partial coverage gives `NO_RECORD`.
- **Missing source is not proof.** A video with no source match gives `NO_RECORD`, never "real".
- **Text inside images is data.** Any instruction found in a screenshot or video is ignored; tests must cover this.
- **Data:** synthetic customers, holdings and transactions in the ReBIT AA format; public SEBI/RBI/NSE/BSE lists; teammates' consented video. No real customer data. No real person's data or likeness. Every mock (AA, Suspect Registry, @valid lookup, payments ledger, official footage) is labelled as a mock in code, UI and docs.
- **Never hard-code a result.** Every screen comes from the real pipeline. `LLM_PROVIDER=cache` may replay only the claim reader's stored output.
- **Source log:** every downloaded public file gets a row in `data/SOURCES.md` (source page, download date, SHA-256). Do not commit large copies of public lists.
- **Frozen test set:** `data/frozen/` is written by someone who does not write the verdict rules and is hashed in `data/frozen/HASH.txt`. Never edit it to make a test pass.
- **Git:** no "Claude", "Anthropic" or AI-assistant attribution in commits, PRs or files, and no `Co-Authored-By` lines.
- Never commit `.env`, API keys or large media (>20 MB); media goes in `data/media/` which is git-ignored.

## Stack

- Backend: Python 3.11, FastAPI, Pydantic v2, SQLite, pytest, ruff
- Frontend: React + Vite + TypeScript + Tailwind; one app with routes `/app` (bank app) and `/reviewer` (reviewer console)
- Claim reader: free local models behind `LLM_PROVIDER` = `local` (default: EasyOCR hi+en, then Ollama gemma3:4b with qwen2.5:3b as fallback) | `cache` | `offline` (Tesseract with Hindi pack + regex). Demo runs on `cache`; a failed `local` read falls back to `offline`. No paid APIs.
- Video: ffmpeg, perceptual hashes (imagehash) + CLIP/DINOv2 frame embeddings, locally run Whisper (small or medium weights, pre-downloaded) for transcripts
- UI font: Noto Sans Devanagari bundled locally so Hindi renders without internet
- Offline kit: `wheels/` (pip download -r requirements.txt -d wheels/), npm cache, model weights; nothing may need the network at demo time
- Evidence: SHA-256 hash chain, stored encrypted (Fernet) in SQLite

## Layout

```
backend/app/
  main.py            FastAPI app and routes
  schemas/           claims.py, verdict.py, evidence.py  (shared contracts: lead only)
  reader/            artifact -> claims (LLM + cache)
  router/            claim -> which record to check
  connectors/        aa_mock.py, isin_master.py, sebi.py, rbi.py, upi.py, suspect_registry.py, footage_index.py
  comparators/       holdings.py, video.py
  verdict/           rules.py (lead only)
  templates/         messages_en.json, messages_hi.json
  evidence/          hashchain.py, pack.py
backend/tests/
frontend/src/        pages/BankApp, pages/Reviewer, components/ResultScreen
data/registries/     cached public lists (CSV): SEBI intermediaries, RBI Alert List, NSE/BSE equity lists (name -> ISIN)
data/SOURCES.md      source page, download date, SHA-256 for every public file
data/schemas/        ReBIT AA equities and mutual-funds schemas (copied for reference, with source and date)
data/frozen/         frozen test set + HASH.txt (not written by the rule author)
data/synthetic/      customers, AA FI data (ReBIT format), portfolios
data/demo_cache/     cached LLM outputs for demo screenshots
data/media/          videos and screenshots (git-ignored)
scripts/             seed, generate portfolios, build footage index, make fakes
```

## Commands

```bash
# backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
pytest -q
ruff check . && ruff format .

# frontend
cd frontend && npm install && npm run dev      # http://localhost:5173

# data
python scripts/fetch_registries.py             # cache SEBI/RBI/NSE lists
python scripts/gen_portfolios.py --n 300 --seed 42
python scripts/build_footage_index.py data/media/official/
```

## Conventions

- Every connector returns `RecordResponse(source, fetched_at, consent_id, payload, sha256)`; the evidence chain stores it as-is.
- Every verdict carries `reason_code` (e.g. `HOLDING_NOT_FOUND_ALL_DEPOSITORIES`) that maps to one template key in both languages.
- Indian number format for money in the UI (₹3.98 crore, ₹1,07,000).
- Tests: each rule has one MATCHES, one CONTRADICTS, one NO_RECORD and one adversarial case.
- Small commits with plain messages: `verdict: add partial-coverage rule`.
