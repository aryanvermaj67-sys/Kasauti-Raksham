# Kasauti (कसौटी)

**AI can fake what you see. It cannot fake the record.**

A kasauti is the black touchstone goldsmiths use to test gold against a known standard. Kasauti does the same to AI investment scams: inside a bank's own app, it tests every claim in an ad or a trading-app screenshot against a record the scammer cannot change, and shows the mismatch as plain facts in Hindi or English.

> Amazon AI Cyber Security Hackathon, IIT Delhi · Track 03: Deepfake Detection for Financial Communications · Team Alpha, Chitkara University

| | |
|---|---|
| What it is | A verification layer for a bank app: read claims, test them against records, show facts, give a safe path to report |
| What decides | Fixed rules. The language model only reads an image into claims; it never decides a verdict or writes the message |
| Verdicts | Exactly three: **Matches the record**, **Contradicts the record**, **No record found**. Never "safe", "verified" or "genuine"; never a percentage |
| Runs | Offline, on one laptop, with free local models. No paid API, no cloud call |
| Status | Working prototype, tested on synthetic data and the public SEBI, RBI, NSE and BSE lists. Account Aggregator, Suspect Registry, @valid lookup, payments ledger and official footage are labelled mocks |

---

## Contents

1. [The problem](#1-the-problem)
2. [What Kasauti does](#2-what-kasauti-does)
3. [How it works: the technical flow](#3-how-it-works-the-technical-flow)
4. [The verdict rules](#4-the-verdict-rules)
5. [The video source check](#5-the-video-source-check)
6. [Evidence, privacy and safety](#6-evidence-privacy-and-safety)
7. [Tech stack](#7-tech-stack)
8. [Install and run](#8-install-and-run)
9. [Screens and demo](#9-screens-and-demo)
10. [Configuration](#10-configuration)
11. [API](#11-api)
12. [Tests and measured results](#12-tests-and-measured-results)
13. [Data: what is real and what is mock](#13-data-what-is-real-and-what-is-mock)
14. [Repository layout](#14-repository-layout)
15. [Known limits and next steps](#15-known-limits-and-next-steps)
16. [Documentation index](#16-documentation-index)
17. [Team](#17-team)

---

## 1. The problem

Investment fraud is most of India's cyber-fraud loss: ₹22,495 crore was lost to cyber fraud in 2025 and over 75% of it was investment scams (Ministry of Home Affairs data, reported by ThePrint, 21 Feb 2026).

The pattern: an AI-made endorsement video of a public figure → an "advisor" on WhatsApp or Telegram → a fake trading app whose dashboard shows a growing portfolio → repeated transfers to rotating personal accounts → a "tax" demanded before any withdrawal. The victim keeps paying because the ad and the dashboard look real. In one reported Pune case the app showed nearly ₹3.98 crore and the victim had lost ₹1.07 crore.

Today's tools do not stop the next transfer. A deepfake detector gives a probability that the scammer can argue away. SEBI Check only helps a customer who thinks to use it. The bank blocks only payees already in the Suspect Registry, and a fresh mule account is not listed yet.

**Kasauti's idea:** the scammer controls the screen, not the record. Put the claim next to the record, at the moment of payment.

## 2. What Kasauti does

A customer partway through a scam opens the bank app and taps **Check**, or the bank prompts them because a payment fits the scam pattern. They share the ad or app screenshot (and optionally the video). Kasauti then:

1. **Reads** the claims in the artifact: holdings, broker, payee, platform, and the endorsing speech.
2. **Lets the customer confirm** the list and fix any misreading.
3. **Tests** each claim against the record that settles it:

| Claim in the ad or app | Record that settles it |
|---|---|
| "You hold 5,000 shares worth ₹3.98 crore" | Depository holdings (CDSL and NSDL) through Account Aggregator, with the customer's consent |
| "Zyphra Stock Club, SEBI registered" | SEBI's register of intermediaries (brokers, advisers, research analysts) |
| "Pay this UPI ID" | SEBI @valid broker handles; the I4C Suspect Registry |
| "The minister recommends it" (video) | The official footage the clip was cut from: is it the original, and were the words changed? |
| "Licensed forex app" | RBI Alert List of unauthorised forex platforms |

4. **Reveals** the result in two columns, in Hindi or English: *your app says ₹3.98 crore; your record says none of it is in your name.* No score, no badge.
5. **Acts**: a pre-filled complaint for 1930 and cybercrime.gov.in, a call to a trusted family member, a bank callback. A hash-chained evidence pack goes to a bank reviewer, who decides whether to report the payee and warn other customers who paid it. Nothing is ever blocked automatically.

## 3. How it works: the technical flow

```
customer phone ──► bank app (React, Hindi / English)
                      │  screenshot (+ video)
                      ▼
 ┌─ CLAIM READER  backend/app/reader ────────────────────────────────────────────────┐
 │ EasyOCR (hi+en) ─► text repairs ─► Tesseract second reading (UPI ids, reg. no.)   │
 │ ─► local LLM (gemma3:4b, fallback qwen2.5:3b) answers in a FIXED JSON schema      │
 │ ─► code validates, repairs and grounds every field (the model only proposes)      │
 └───────────────────────────────────┬────────────────────────────────────────────────┘
                 customer confirms / edits the claims on screen
                                     ▼
 CLAIM ROUTER  backend/app/router ─► picks the record for each claim
                                     ▼
 CONNECTORS  backend/app/connectors  (each returns RecordResponse: source, time, consent id, payload, SHA-256)
   holdings ─ aa_mock        Account Aggregator, ReBIT format, CDSL + NSDL            MOCK
   broker   ─ sebi           SEBI registers (5,000+ brokers, advisers, analysts)      real public list
   payee    ─ upi, suspect_registry   @valid handle format; I4C Suspect Registry      MOCK
   platform ─ rbi            RBI Alert List (95 names)                                real public list
   video    ─ footage_index  official footage index (picture + sound)                 teammates' consented clips
                                     ▼
 COMPARATORS  backend/app/comparators   holdings by ISIN · video: source finder + changed-words (audio)
                                     ▼
 VERDICT ENGINE  backend/app/verdict/rules.py   rules only → MATCHES / CONTRADICTS / NO_RECORD + reason code
                                     ▼
        fixed templates (EN / HI) ─► result screen          evidence store: SHA-256 hash chain,
        reviewer console ─► approve / reject ─► registry     Fernet-encrypted SQLite, access logged
```

### 3.1 Claim reader (`backend/app/reader`)

- **Providers** (`LLM_PROVIDER`): `local` (default: EasyOCR + Ollama), `cache` (replays stored reader output for the three demo screenshots only), `offline` (Tesseract + regular expressions). A failed `local` read falls back to `offline` and the evidence pack records the fallback.
- **The model only proposes.** Its output must validate against `docs/formats/claims.schema.json`. Code then repairs and grounds it: ISINs misread with O for 0 are repaired by the ISIN check digit and only to an ISIN that exists on the NSE or BSE list; lost decimal points and spaces inside numbers are repaired; a "registered" claim the page does not make is removed; an ISIN copied onto two holdings stays on one; numbers the OCR text does not show are dropped; the holdings are checked against the printed total, with one retry if a line is missing; invalid IFSC or account digits are repaired or dropped.
- **Text in images is data, never instruction.** A claim that reads like an instruction is dropped, and in any case no model output can reach a verdict. Tested with English and Hindi injections.

### 3.2 Router and connectors (`router`, `connectors`)

The router maps each confirmed claim to its record and asks the customer to choose when a share name matches several listed securities. Every connector returns a `RecordResponse` that the evidence chain stores as it is. A share name is mapped to an ISIN only when exactly one listed security matches.

### 3.3 Verdict engine (`verdict/rules.py`)

The only module that can build a verdict (a test proves it). Every verdict carries a `reason_code` that maps to one template in `messages_en.json` and `messages_hi.json`, so every sentence the customer reads is fixed text. See [section 4](#4-the-verdict-rules).

### 3.4 Evidence and response (`evidence`, `reviewer`, `trigger`)

Hash-chained, encrypted evidence; a reviewer console with approve and reject; the Suspect Registry write (mock) that warns other customers who paid the same payee; a scam-pattern trigger over the payments ledger (behaviour only, at most one prompt per campaign per customer).

## 4. The verdict rules

| Claim | MATCHES | CONTRADICTS | NO_RECORD |
|---|---|---|---|
| **Holding** | ISIN and quantity found at a depository | Not found, or quantity differs, **and every depository in scope answered** (including: both answered and there is no demat account at all) | A depository failed or is out of scope; the customer skipped consent; the name matches several listed securities; the ISIN is on neither list (likely a misread) |
| **Broker** | Exact normalised name on the SEBI list; a quoted registration number must belong to that name | Says it is registered but is not on the list; or a registration number that belongs to another firm (a borrowed number) | One typo away from a registered firm ("not identical to"); not on the list but never claimed to be registered |
| **Payee** | A SEBI @valid broker handle that is not in the Suspect Registry (mock lookup) | In the Suspect Registry; or described as a broker but not an @valid handle | Any other UPI ID, or a bank account: nothing says who owns it |
| **Platform** | never | On the RBI Alert List | Not on the list |
| **Endorsement (video)** | Source found by the picture (or picture and sound) and the audio has no changed span | Source found and the audio differs in a span: the time range and the original words are shown | No source found; found by sound alone with the same words (a real voice under another picture is the classic fake) |

Hard rules, each enforced by a test:

- **No false contradiction.** A holding contradicts only if every depository in the consent scope answered successfully.
- **Missing source is not proof.** A video with no source gives "no record found", never "real".
- **Three outcomes only.** No code path or template contains "safe", "verified" or "genuine", and no percentage is ever a verdict.
- **Broker names are normalised** (case, punctuation, legal words such as ltd and pvt dropped); one typo anywhere gives "not identical to", never a contradiction; look-alike glyphs never match.

## 5. The video source check

Not a deepfake detector: it finds the original footage a clip was cut from, and what changed.

1. **Find the source.** One frame per second, CLIP ViT-B/32 embeddings (plus a 90% centre crop of every official frame) and an audio fingerprint of the soundtrack. Either signal can find the source; if the picture points to one clip and the sound to another, there is no single source.
2. **Find what changed.** A calibrated log-mel aligner compares the upload with the source after aligning the two; spans that differ are the changed words.
3. **Quote it.** faster-whisper transcribes only the flagged span, so the screen shows the new words and the original ones.
4. **Be honest.** A fully AI-generated video has no source and gives "no record found". Heavy edits may be missed and give "no record", never "matches". There is no lip-sync or voice-clone analysis.

## 6. Evidence, privacy and safety

- **Hash chain.** Each record response is stored with source, time, consent ID, SHA-256 and the previous hash; one changed byte breaks verification (tested). Stored in SQLite, encrypted with Fernet, access logged, 30-day retention. The evidence pack lists the hashes a Section 63(4) certificate needs; it is not a legal certificate.
- **Consent.** Holdings are fetched once, with a one-time OTP (mock in the prototype), then deleted. The chain keeps hashes and which claimed ISINs were found, never the holdings. The Account Aggregator mock returns the holdings summary only, never PAN, mobile number or transactions.
- **Not collected:** contacts, gallery, calls, messages, location, transaction history, balances.
- **Never blocks, never accuses.** The customer decides every payment and sends any complaint. A bank reviewer must approve before an account goes to the Suspect Registry or other customers are warned.
- **Results only inside the bank app**, never by SMS, call or link, and there is no shareable "verified" badge, so a scammer cannot imitate them.
- **Reviewer role** is a mock header in the prototype (no login); the backend still refuses evidence to any other role (403). A bank would use its staff single sign-on.
- **Offline.** The demo run blocks every non-loopback connection (`scripts/offline_guard`), and models load only from local folders.

## 7. Tech stack

| Layer | Tools |
|---|---|
| Backend | Python 3.11 or newer (developed on 3.14), FastAPI, Pydantic v2, SQLite, httpx, cryptography (Fernet), pytest, ruff |
| Frontend | React, Vite, TypeScript, Tailwind CSS, Noto Sans Devanagari and Inter (bundled, so Hindi renders offline) |
| Claim reading | EasyOCR (Hindi + English), Tesseract with the Hindi pack (second reading and offline fallback), Ollama running `gemma3:4b` (fallback `qwen2.5:3b`) |
| Video | ffmpeg, OpenCLIP ViT-B/32 (laion2b), imagehash, faster-whisper (small), a log-mel aligner and audio fingerprint written for this project |
| Evidence | SHA-256 hash chain, Fernet encryption, SQLite |
| Data | Public SEBI, RBI, NSE and BSE lists; ReBIT Account Aggregator schemas; synthetic customers and portfolios |

## 8. Install and run

### 8.1 Prerequisites

- Python 3.11 or newer, Node.js 20 or newer, ffmpeg on the PATH.
- [Ollama](https://ollama.com) with `gemma3:4b` and `qwen2.5:3b` pulled; EasyOCR weights; Tesseract with the Hindi pack (optional, for the offline fallback). Step by step: [docs/SETUP_LOCAL_MODELS.md](docs/SETUP_LOCAL_MODELS.md).
- An NVIDIA GPU with about 8 GB is recommended (a read takes 2 to 7 s). Without one a read takes 20 to 80 s; set `CUDA_VISIBLE_DEVICES=-1`.

### 8.2 Install

```bash
git clone https://github.com/aryanvermaj67-sys/Kasauti-Raksham.git
cd Kasauti-Raksham
cp .env.example .env            # then set EVIDENCE_KEY (see below)

pip install -r backend/requirements.txt -r backend/requirements-local.txt -r backend/requirements-video.txt
cd frontend && npm install && cd ..

python scripts/fetch_registries.py             # public SEBI / RBI / NSE lists (needs the internet once)
python scripts/gen_portfolios.py --n 300 --seed 42
ollama pull gemma3:4b && ollama pull qwen2.5:3b
python scripts/check_local_models.py           # must print "local models OK"
```

`EVIDENCE_KEY` is a Fernet key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. If it is empty, a dev key file is created next to the database.

### 8.3 Run

```bash
# backend (terminal 1)
cd backend && python -m uvicorn app.main:app --port 8000

# frontend (terminal 2)
cd frontend && npm run dev -- --port 5173
```

Add `KASAUTI_DEMO=1` to the backend's environment to enable the presenter buttons (`/demo/run`, `/demo/reset`). The backend warms its models in the background; `GET /health` says `ready` when the reader and the video models are loaded (the first call after a cold start can take 100 s or more).

### 8.4 Files a fresh clone does not have (git-ignored)

Copy them from a teammate or the pen-drive kit; `scripts/make_kit.ps1` and `scripts/restore_kit.ps1` pack and restore all of them with a SHA-256 manifest.

| Copy to | Needed for | If missing |
|---|---|---|
| `.env` | evidence key | a dev key file is used |
| `data/registries/bse_equity.csv` | ISIN mapping (BSE only answers a browser session, so `fetch_registries.py` cannot fetch it) | the API cannot map names to ISINs |
| `models/open_clip/`, `models/whisper/` | video frame embeddings and transcripts (about 1 GB) | video tests skip; `/api/video` fails |
| `data/footage_index/` (`clips.json`, `embeddings.npy`, `owner.npy`, `audio.npz`) | the MOCK footage index; or rebuild: `python scripts/build_footage_index.py data/media/official/` | `/api/video` answers 503 |
| `data/media/` (official clips, test clips, fake apps) | video demo and tests | video tests skip |
| `wheels/` | offline `pip install --no-index --find-links wheels ...` | needs the network |

### 8.5 One-command demo

```bash
scripts/reset_demo.sh      # Windows: scripts\reset_demo.ps1. Clears evidence, dev key, MOCK registry additions
python scripts/preflight.py   # Windows: scripts\preflight.ps1. One line per check, prints GO or NO-GO
scripts/demo.sh            # Windows: scripts\demo.ps1 [--cpu]. Starts both servers, runs every flow, prints "demo OK offline"
```

On the reference laptop (RTX 5050, 8 GB) the whole offline run passes with a full video result in about 9 seconds (source search about 1.2 s).

## 9. Screens and demo

| Route | What it is |
|---|---|
| `/app` | Customer app, 8 steps: Pay, Upload, Confirm, Consent, Checking, Result, Action, Pack. English and Hindi, larger-text mode. `?customer=SYN-C0028` picks the synthetic customer whose records are checked |
| `/reviewer` | Bank reviewer console: verdict counters, queue of checks with a contradiction, claims against records, hash-chain check, approve or reject, evidence pack export |
| `/present` | Phone and console side by side in one tab, with Run demo-001, 002, 003 and Reset demo buttons (need `KASAUTI_DEMO=1`) |

Every value on these screens comes from the API; every sentence from `backend/app/templates`. The mock one-time code is `123456`.

Where to start:

- [docs/DEMO.md](docs/DEMO.md): the 3-minute script with on-screen text and the Q&A sheet.
- [docs/DEMO_INPUTS.md](docs/DEMO_INPUTS.md): every input to type and upload, real and fake, with the result each one gives, including the same screenshot run three ways to fill all three counters.
- [docs/DEMO_DAY.md](docs/DEMO_DAY.md): the start order, waits and what to do when something fails.

## 10. Configuration

| Variable | Values | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `local` (default), `cache`, `offline` | Claim reader. Use `local` for live input; `cache` only replays the three demo screenshots |
| `KASAUTI_LOCAL_MODEL`, `OLLAMA_HOST` | `gemma3:4b`, `http://127.0.0.1:11434` | Model and server for `local`; loopback only |
| `KASAUTI_KEEP_ALIVE`, `KASAUTI_READ_TIMEOUT` | `60m`, `60` (seconds, times 3 on a machine with no GPU) | Keep the model loaded; model time limit |
| `EVIDENCE_KEY` | Fernet key | Encrypts the evidence store |
| `RETENTION_DAYS` | `30` | Evidence retention |
| `REGISTRY_DIR` | path | Cached SEBI, RBI and NSE lists (default `data/registries`) |
| `KASAUTI_DEMO` | `1` | Enables `POST /demo/run` and `POST /demo/reset` |
| `KASAUTI_PRELOAD_VIDEO` | `1` (default) | Load the video models at startup |
| `HF_HUB_OFFLINE`, `KASAUTI_ALLOW_DOWNLOAD` | `1`, `1` | Models load only from `models/`; set the second to `1` only to download them once |

## 11. API

| Method and path | Purpose |
|---|---|
| `GET /health`, `GET /api/health` | Readiness and which models are still loading |
| `POST /api/read` | Screenshot to a validated claim set (fixed schema) |
| `POST /api/video` | Video to the source match and changed spans; stored as the footage evidence record |
| `GET /api/isin/candidates` | Listed securities matching a share name |
| `POST /api/check` | Confirmed claims plus customer and consent to verdicts, summary messages and the stored check |
| `GET /api/checks/{id}/records`, `GET /api/checks/{id}/pack` | The records behind a check; the evidence pack |
| `GET /api/reviewer/queue`, `GET /api/reviewer/checks/{id}` | Reviewer queue and detail (reviewer role only) |
| `POST /api/reviewer/checks/{id}/approve`, `.../reject`, `.../pack` | Reviewer decisions and pack export |
| `GET /api/registry/lookup` | Suspect Registry look-up (mock) |
| `GET /api/trigger/{customer}`, `POST .../ack` | Scam-pattern prompt for a customer and its acknowledgement |
| `GET /cases`, `GET /stats` | Console lists and counters (verdicts, prompts per 1,000 customers, median time) |
| `GET /demo/scenarios`, `POST /demo/run`, `POST /demo/reset` | Presenter view (demo mode only) |

Interactive docs at `http://localhost:8000/docs`. The shared contracts are `backend/app/schemas/` (claims, verdicts, evidence) and `docs/formats/`.

## 12. Tests and measured results

Run everything: `sh scripts/verify_all.sh` (add `--quick` to skip the demo and validation runs). Backend only: `cd backend && python -m pytest -q`. Frontend: `cd frontend && npm test`.

| Test | Result |
|---|---|
| Backend tests, lint, templates (EN/HI), frontend build, lint and tests, offline demo | all pass (167 backend tests, 6 skipped when optional files are missing; 7 frontend) |
| Verdict rules on 300 synthetic portfolios (fake, mixed, real, no demat, partial coverage), 1,261 holding claims | 300 of 300 |
| Frozen set written by someone who does not write the rules (130 rule cases, 76 brokers, 20 payees, 9 injected-text images, 64 screenshots) | 274 of 274 verdicts; **0 false contradictions out of 165** items that should not contradict; screenshot fields 608 of 632 (96%); injection 5 of 5 |
| 60 generated full-screen fake apps (6 layouts, English and Hindi) | 573 of 584 fields (98%) |
| 12 realistic fake apps from an image generator (an unseen style) | 103 of 104 fields |
| Video, the team's own clips (8 official clips, 62 variants; not independent) | source found 40 of 40 across re-upload, low quality, crop, banner and trim; changed words found 16 of 16; no-source clips give "no record" 6 of 6; 0 false "changed words" |
| Speed, offline demo, GPU | full result with video about 9 s |

The frozen set was used to find and fix bugs between runs (the first run had 14 false contradictions; the final run has none), so it is **not a blind test**; the run history is in [docs/VALIDATION_SUMMARY.md](docs/VALIDATION_SUMMARY.md). Every number can be reproduced from a fresh clone with the commands in [docs/TEST_KIT.md](docs/TEST_KIT.md), which also lists the failure cases.

## 13. Data: what is real and what is mock

| Item | Status |
|---|---|
| SEBI registers (brokers, advisers, research analysts), RBI Alert List, NSE and BSE equity lists, ReBIT Account Aggregator schemas | **Real public data**, cached locally; each file has a row in `data/SOURCES.md` with source page, date and SHA-256 |
| Account Aggregator holdings, I4C Suspect Registry, SEBI @valid lookup, payments ledger, official footage | **Mock**, labelled MOCK in the code, the UI and the docs. The real systems are not public |
| Customers, holdings, transactions, portfolios | **Synthetic**, in the ReBIT format, generated from public lists with a fixed seed |
| Firms, platforms, UPI handles in the demo | Invented (only the listed company names, SEBI and RBI examples used in the demo inputs are real public records) |
| Videos | Teammates' own consented recordings; no real public figure's face or voice is used |
| Fake-app screenshots | Generated by a script and by an image generator; AI-generated images are disclosed as such |

No real customer, bank or platform data is used anywhere.

## 14. Repository layout

```
backend/
  app/
    main.py            FastAPI app and routes
    schemas/           claims, verdicts, evidence: the shared contracts
    reader/            claim reader: local (EasyOCR + Ollama), offline (Tesseract), cache
    router/            claim to record; runs a check
    connectors/        aa_mock, isin_master, sebi, rbi, upi, suspect_registry, footage_index
    comparators/       holdings, video (picture + sound), audio (fingerprint and aligner)
    verdict/           rules.py: the only place a verdict is built
    templates/         messages_en.json, messages_hi.json: every sentence the customer reads
    evidence/          hash chain, pack export
    reviewer.py, trigger.py, ledger.py, demo_reset.py
  tests/               rule, reader, video, evidence, API, offline-guard and data-contract tests
frontend/src/          pages (CustomerApp, Reviewer, Present), components, i18n
data/
  registries/          cached public lists (SEBI, RBI, NSE; BSE copied in)
  synthetic/           portfolios, ledger, mock Suspect Registry
  schemas/             ReBIT Account Aggregator schemas
  frozen/              the frozen test set and HASH.txt (never edited)
  demo_cache/          the three demo screenshots and their stored reader output
  media/               videos and screenshots (git-ignored)
scripts/               data generators, evaluation and validation runners, demo, preflight, kit
docs/                  test kit, validation runs, demo scripts, judging and deck notes, formats
PRD.md                 requirements
progress.md            live build status and decisions log
```

## 15. Known limits and next steps

- Consent is voluntary: a victim who will not share a screenshot is not checked. The bank can prompt but never force.
- Crypto and forex claims have no holdings record; only the RBI Alert List and payee checks run.
- The video check works only against an archive of official footage. In the demo the archive holds the team's own clips; a deployment needs an index of public footage of public figures. Fully generated videos and heavy edits give "no record found", never "real" or "matches". Not yet tested on independent real-world videos.
- A read takes 20 to 80 s on a machine with no GPU; GPU memory is tight when everything is loaded.
- The reviewer login is a mock header, and the Hindi screen strings still need a native-speaker review.
- Account Aggregator, the Suspect Registry and the @valid lookup are mocks; the prototype does not connect to any bank or regulator system.

Next: independent video testing; a first-time-payee signal from the bank's own ledger; a public-footage index; a native Hindi review of every string; load testing beyond one laptop; the cloned-voice family check as an extension.

## 16. Documentation index

| Topic | File |
|---|---|
| Requirements and decisions | [PRD.md](PRD.md), [progress.md](progress.md) |
| Local model setup | [docs/SETUP_LOCAL_MODELS.md](docs/SETUP_LOCAL_MODELS.md) |
| Reproduce every result, error rates, failure cases | [docs/TEST_KIT.md](docs/TEST_KIT.md), [docs/VALIDATION_SUMMARY.md](docs/VALIDATION_SUMMARY.md), [docs/VIDEO_EVAL.md](docs/VIDEO_EVAL.md) |
| Frozen test set rules | [docs/FROZEN_SET_SPEC.md](docs/FROZEN_SET_SPEC.md) |
| Demo | [docs/DEMO.md](docs/DEMO.md), [docs/DEMO_INPUTS.md](docs/DEMO_INPUTS.md), [docs/DEMO_DAY.md](docs/DEMO_DAY.md) |
| Judging and presentation | [docs/JUDGING_PLAN.md](docs/JUDGING_PLAN.md), [docs/DECK_FIXES.md](docs/DECK_FIXES.md), [docs/jury_pack/KASAUTI_JURY_PREP.pdf](docs/jury_pack/KASAUTI_JURY_PREP.pdf) |
| UI integration | [docs/UI_INTEGRATION.md](docs/UI_INTEGRATION.md) |
| Hindi message review | [docs/HINDI_REVIEW.md](docs/HINDI_REVIEW.md) |
| Data sources | [data/SOURCES.md](data/SOURCES.md) |
| JSON contracts | [docs/formats/](docs/formats/) |

## 17. Team

Team Alpha, Chitkara University: Aryan Verma · Himanil Datyal · Mudit Gupta · Rajat Gupta.

A hackathon submission: all customer data is synthetic and every mock is labelled. No licence has been set for reuse.
