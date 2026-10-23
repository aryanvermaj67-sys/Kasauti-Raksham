# Kasauti (कसौटी)

**AI can fake what you see. It cannot fake the record.**

A kasauti is the black touchstone goldsmiths use to test gold against a known standard. Kasauti does the same to AI investment scams: it tests every claim in an ad or trading app against a record the scammer cannot change.

> Amazon AI Cyber Security Hackathon, IIT Delhi · Track 03: Deepfake Detection for Financial Communications · Team Alpha, Chitkara University

---

## What it does

A customer partway through a fake-investment scam opens their bank app and taps **Check**, or the bank prompts them because a payment fits the scam pattern. They share the ad or the app screenshot. Kasauti:

1. **Reads** the claims: holdings, broker, payee, the person endorsing it, the platform.
2. **Tests** each claim against the record that settles it:
   | Claim | Record |
   |---|---|
   | "You hold 3 stocks worth ₹3.98 crore" | Depository holdings via Account Aggregator |
   | "Zyphra Stock Club, SEBI-registered" | SEBI registered intermediaries |
   | "Pay this UPI ID" | SEBI @valid handles, I4C Suspect Registry |
   | "The minister recommends it" | Official footage the clip was cut from |
   | "Licensed forex app" | RBI Alert List |
3. **Reveals** the result side by side, in Hindi or English: *Your app says ₹3.98 crore. Your record says ₹0.* No score, no "safe" badge.
4. **Acts**: a pre-filled 1930 complaint, a call to a trusted contact, or a bank callback. A hashed evidence pack goes to a bank reviewer, who decides whether to escalate.

Every verdict is one of **Matches the record**, **Contradicts the record**, or **No record found**. Fixed rules decide; the language model only reads claims.

## Architecture

```
Bank app ──► Claim reader (vision LLM, fixed schema)
                │
                ▼
            Claim router ──► Record connectors ──► AA (mock) · SEBI · RBI · UPI · Suspect Registry · Footage index
                │                     │
                ▼                     ▼
            Comparators (holdings, video) ──► Verdict engine (rules only)
                                                   │
                       ┌───────────────────────────┼──────────────────────────┐
                       ▼                           ▼                          ▼
                Result screen (EN/HI)       Evidence store (hash chain)   Reviewer console
```

Personal data stays in the bank. Outside records are only read; the single write is a reviewer-approved Suspect Registry entry.

## Tech stack

| Layer | Tools |
|---|---|
| Backend | Python 3.11, FastAPI, Pydantic v2, SQLite |
| Frontend | React, Vite, TypeScript, Tailwind |
| Claim reading | Vision LLM (Amazon Nova on Bedrock or Claude), with an offline cache mode |
| Video | ffmpeg, imagehash, CLIP / DINOv2 embeddings, faster-whisper |
| Evidence | SHA-256 hash chain, Fernet encryption |
| Tests | pytest, ruff |

## Quick start

```bash
git clone https://github.com/aryanvermaj67-sys/kasauti.git
cd kasauti
cp .env.example .env            # set LLM_PROVIDER=cache for offline demo

# backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python ../scripts/fetch_registries.py
python ../scripts/gen_portfolios.py --n 300 --seed 42
uvicorn app.main:app --reload --port 8000

# frontend (new terminal)
cd frontend
npm install
npm run dev                     # bank app: http://localhost:5173/app · reviewer: /reviewer
```

Run tests: `cd backend && pytest -q`

Requires ffmpeg on PATH for the video check.

## Environment variables

| Variable | Values | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `cache` · `bedrock` · `anthropic` | Claim reader backend; `cache` needs no network |
| `AWS_REGION`, `BEDROCK_MODEL_ID` | | For `bedrock` |
| `ANTHROPIC_API_KEY` | | For `anthropic` |
| `EVIDENCE_KEY` | Fernet key | Encrypts the evidence store |
| `REGISTRY_DIR` | path | Cached SEBI/RBI/NSE lists (default `data/registries`) |

## Demo script (3 minutes)

1. A deepfake ad of a "public figure" (a teammate, with consent) promotes a trading app.
2. The fake app shows a ₹3.98 crore portfolio and asks for another deposit.
3. In the bank app, the customer taps **Check** and uploads the screenshot and the ad.
4. Claims appear; he confirms them and gives OTP consent.
5. Result: **0 of 3 holdings found in your record** · **broker not on SEBI's list** · **ad cut from an official speech, words changed at 0:14–0:32**.
6. He taps **Report to 1930**; the complaint is pre-filled.
7. The reviewer opens the evidence pack, sees the hash chain is intact, approves, and the payee is listed.

## Repository layout

```
backend/     FastAPI service: reader, router, connectors, comparators, verdict, evidence
frontend/    Bank app and reviewer console
data/        Cached public registries, synthetic data, demo cache (media is git-ignored)
scripts/     Data fetch, synthetic generation, footage index, fake generation
docs/        Pitch deck and architecture notes
PRD.md       Requirements
progress.md  Live build status
```

## Data and ethics

- Customers, transactions and holdings are synthetic, in the Account Aggregator (ReBIT) format.
- SEBI, RBI and NSE/BSE lists are public; cite them and do not redistribute large copies.
- The "public figure" in demo videos is a teammate who gave written consent. No real public figure is faked.
- No bank, customer or platform data is used.

## Known limits

- Consent is voluntary, so some victims will never run a check.
- Crypto and forex claims have no holdings record; only registry and payee checks apply.
- Fully generated videos have no source to find; the result is "No record found", never "real".
- Sahamati lists both CDSL and NSDL as providers over Account Aggregator, but a given customer's fetch can still fail or be partial. That case returns **No record found**, never a contradiction.

Each limit falls back to **No record found**, never to a false "safe".

## Data sources

Public: SEBI registered intermediaries, RBI Alert List, NSE and BSE equity lists (name to ISIN), ReBIT Account Aggregator schemas (equities, mutual funds), Sahamati's list of data providers. Each file's source page, download date and SHA-256 is recorded in `data/SOURCES.md`. Mocked and labelled as such: Account Aggregator data, the I4C Suspect Registry, SEBI @valid lookups, bank payment records and official footage.

## Team Alpha

Aryan Verma · Himanil Datyal · Mudit Gupta · Rajat Gupta — Chitkara University
