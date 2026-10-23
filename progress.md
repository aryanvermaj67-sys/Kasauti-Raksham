# Kasauti — Progress

> Maintained by the `progress-keeper` agent. Humans may edit; keep the section headings.

## Status

| | |
|---|---|
| Phase | 0 · Setup |
| Overall | 12% |
| Demo-ready | No |
| Last updated | 23 Oct 2026, 18:07 IST |

## Team and ownership

| Role | Owner | Area |
|---|---|---|
| A | _fill_ | Fake trading app, synthetic data, consented videos |
| B | _fill_ | Claim reader, video source finder |
| C | _fill_ | Backend: connectors, verdict rules, evidence chain |
| D | _fill_ | Bank app UI, reviewer console, pitch |

## Pre-finale checklist (before 24 Oct)

**Rules to confirm with organisers**
- [ ] Pre-written code allowed, or only data, designs and models?
- [ ] Venue internet, power, paid cloud APIs allowed?
- [ ] Registered track matches the deck (Track 03)

**Accounts and keys (test on a fresh laptop)**
- [ ] Hosted vision model chosen (Claude API or Amazon Nova on Bedrock); credits and rate limits checked
- [ ] Offline fallback: Tesseract + Hindi pack + regex patterns
  - [x] Tesseract 5.4 installed at `C:\Program Files\Tesseract-OCR` with eng, hin (tessdata_fast), osd; not on PATH (set path in config)
  - [ ] Regex patterns
- [ ] Whisper weights (small or medium) and ffmpeg installed

**Data to download (log in data/SOURCES.md: URL, date, SHA-256)**
- [x] SEBI registered intermediaries, scraped by `scripts/fetch_sebi.py` (needs `--ip 202.191.181.158` on a laptop whose DNS cannot resolve sebi.gov.in); counts match SEBI's stated totals
  - [x] `sebi_brokers.csv` (5002, equity segment)
  - [x] `sebi_investment_advisers.csv` (1062)
  - [x] `sebi_research_analysts.csv` (2324)
- [x] RBI Alert List: `data/registries/rbi_alert_list.csv`, 95 entries, 19 Nov 2025 version, hand-typed from PDF (spot-check recommended)
- [x] NSE and BSE equity lists, name to ISIN
  - [x] NSE: `data/registries/nse_equity.csv`
  - [x] BSE: `data/registries/bse_equity.csv` (5120 rows, fetched via Chrome)
- [x] ReBIT AA schemas: equities and mutual funds (`data/schemas/rebit_equities.html`, `rebit_mutual_funds.html`)
- [x] `data/SOURCES.md` rows filled for the files above
- [ ] Sahamati page saved (screenshot + date) for "CDSL and NSDL provide data over AA"

**Offline kit**
- [ ] CLIP or DINOv2 weights + imagehash
- [ ] `pip download -r requirements.txt -d wheels/`, npm cache, Docker images if used
- [ ] Noto Sans Devanagari font
- [ ] Pen drive with all of the above + backup demo video

**Media and synthetic data**
- [ ] Signed consent forms from every teammate on camera or voice
- [ ] 5–10 "official" speech videos + manipulated versions + compressed/cropped copies (30-video test)
- [ ] ~60 fake-app screenshots, 6 layouts, Hindi + English
- [ ] ~300 synthetic portfolios (fake, mixed, real, no demat, partial coverage)
- [ ] Synthetic payments ledger with scam pattern + mock Suspect Registry
- [ ] Frozen test set written by someone else, hashed

**Design**
- [ ] JSON formats frozen: claims, verdicts, record responses, evidence pack
- [ ] Hindi templates checked by a fluent Hindi reader
- [ ] Owners for roles A–D set

**Facts and deck**
- [ ] Deck fixes: "NSDL to be confirmed" (Pitch 7, Arch 3); fraud figure to ₹22,495 crore / "over 75%" (Pitch 2); drop "and lips" (Pitch 6); Pitch 4 Hindi sentence names only CDSL; Pitch 10 "real public lists" for payee check (@valid and Suspect Registry are mocks)
- [ ] Verify or drop: Supreme Court hash ruling, Singapore 2,700+, FBI 77%, face-swap attribution paper, CBI ABHAY
- [ ] Q&A answers: "isn't this just a lookup?", "fully AI-generated video?", "why would a victim share a screenshot?"

**Logistics**
- [ ] Laptops, chargers, extension board, HDMI/USB-C adapters, a phone, mobile hotspot, college ID

## Phase checklist

### Phase 0 · Setup (hours 0–4)
- [x] Repo docs: CLAUDE.md, README.md, PRD.md, progress.md
- [x] Agent orchestration config (.claude/)
- [ ] Repo on GitHub, everyone can push
- [ ] Shared schemas frozen: `claims.py`, `verdict.py`, `evidence.py` (C)
- [ ] Backend skeleton with stub routes returning sample data (C)
- [ ] Frontend skeleton with `/app` and `/reviewer` routes (D)
- [x] SEBI, RBI, NSE, BSE lists downloaded and cached as CSV (A)
  - [x] RBI Alert List, NSE equity list
  - [x] SEBI intermediaries (brokers, advisers, research analysts), BSE equity list
  - [ ] Decide whether SEBI CSVs are committed (see Decisions log and Blockers)
- [ ] Decide LLM provider (Bedrock Nova vs Claude) and log below (B)
- [ ] `.env.example`, `.gitignore`, requirements.txt, package.json

**Checkpoint:** every service returns sample data end to end.

### Phase 1 · Core slice (hours 4–16)
- [ ] Synthetic portfolios generator, ReBIT format, incl. partial-coverage cases (A)
- [ ] Fake trading app screens + 60 screenshots, 6 layouts (A)
- [ ] Claim reader + cache mode + schema validation (B)
- [ ] AA mock, SEBI, UPI, RBI, Suspect Registry connectors (C)
- [ ] Holdings comparator + verdict rules with full-coverage rule (C)
- [ ] EN/HI templates (D)
- [ ] Result screen (D)

**Checkpoint:** screenshot in → "0 of 3 found" out.

### Phase 2 · Video + evidence (hours 16–28)
- [ ] Consented "official" footage + 30 fakes with compression/crop variants (A)
- [ ] Footage index (pHash + embeddings) (B)
- [ ] Source matcher + transcript diff with time ranges (B)
- [ ] Evidence hash chain + `verify_chain()` + pack export (C)
- [ ] Response actions: 1930 pre-fill, contact, callback (D)
- [ ] Full flow wired: share → confirm → consent → result → act (lead)

**Checkpoint:** whole demo story runs without help.

### Phase 3 · Reviewer + validation (hours 28–40)
- [ ] Reviewer console: queue, detail, approve/reject (D)
- [ ] Rule-correctness suite: 300 portfolios (C)
- [ ] Adversarial tests: injected text, renamed broker, near-duplicate UPI, sourceless video (B, C)
- [ ] Timing runs vs targets (C)
- [ ] Prompt-rate report on synthetic transactions (C)
- [ ] Comprehension test with 5 adults (D)

**Checkpoint:** test results table + prompt rate ready.

### Phase 4 · Freeze (hours 40–48)
- [ ] Code freeze, tag `v1.0-demo`
- [ ] Offline run with `LLM_PROVIDER=cache`
- [ ] Backup demo video recorded
- [ ] Re-verify all cited figures in the deck
- [ ] Pitch rehearsal × 3, Q&A drill (sourceless video, false positives, consent)

## Test results

| Test | Target | Result |
|---|---|---|
| Claim fields read | ≥ 95% | — |
| Rule correctness (300) | 100% | — |
| Source match top-1 (30) | ≥ 90% | — |
| Adversarial | 0 false MATCHES | — |
| Comprehension | 5 / 5 | — |
| Result after consent | < 60 s | — |
| Prompts per 1,000 customers | report | — |

## Decisions log

| Date | Decision | Why |
|---|---|---|
| 23 Oct | FastAPI + React/Vite + SQLite | Fast to build, team knows it, runs offline |
| 23 Oct | Lip-sync analysis dropped from MVP | Not reliable in 48 h; source match + transcript diff is enough for the demo |
| 23 Oct | Holdings CONTRADICTS only with full depository coverage | Avoid telling a real investor their app is lying |
| 23 Oct | Demo runs on cached LLM output and cached registries | Venue Wi-Fi and live APIs are a stage risk |
| 23 Oct | Mock AA covers both CDSL and NSDL | Sahamati's non-banking FIP page (updated 29 May 2026) lists both with equity shares and mutual fund units; earlier "NSDL unconfirmed" assumption dropped |
| 23 Oct | Fraud stat changed to ₹22,495 crore, "over 75%" investment scams | MHA data via ThePrint (21 Feb 2026) is the later, larger total. Deck figure ₹19,813 crore / 77% is also sourced (I4C via IANS, 3 Jan 2026) but is an earlier snapshot |
| 23 Oct | Offline claim-reader fallback: Tesseract (Hindi) + regex; Whisper run locally | Network may fail at the venue |
| 23 Oct | RBI Alert List CSV hand-typed from the 19 Nov 2025 PDF | No machine-readable copy; 95 entries; needs a second-person spot-check against the PDF |
| 23 Oct | SEBI lists fetched by `scripts/fetch_sebi.py` with a pinned IP (`--ip 202.191.181.158`) | Local DNS on one laptop cannot resolve sebi.gov.in; scripted fetch works once the IP is given. Row counts match SEBI's stated totals |
| 23 Oct | OPEN: commit or git-ignore the SEBI CSVs | They total ~2 MB and hold public contact emails/phones; CLAUDE.md says not to commit large copies of public lists. Lead to decide |
| 23 Oct | Run GOALS.md in order: Goal 0, then Goal 1, then Goal 2 | Goal 2 (bank app + result screen) was started but stopped before any code; its prerequisites do not exist yet |

## Blockers

- ~~SEBI intermediaries and BSE equity list need manual download~~ Resolved 23 Oct: both fetched and logged in `data/SOURCES.md`.
- Decision pending: SEBI CSVs (~2 MB, contain public contact emails/phones) in git or not. Owner: lead.
- Tesseract is not on PATH. Code must read the install path from config/env (`C:\Program Files\Tesseract-OCR`) or PATH must be set on each laptop.
- Goal 2 (bank app + result screen) was started but stopped before any code was written. Its prerequisites are missing: no `backend/`, no schemas, no `messages_en.json` / `messages_hi.json`, no `demo-001`, no `/api/check`, no verdict rules, and the project folder is not a git repo yet. Lead decided to run GOALS.md Goal 0 first, then Goal 1, then Goal 2.
- Environment note: Python on this laptop is 3.14.6, but the stack specifies 3.11. Node is 24.19 and npm is 11.17.

## Next up

1. Run Goal 0 (contracts, templates, synthetic data) — lead
2. Decide on committing SEBI CSVs, then `git init`, push repo and add all four members — Aryan
3. Second-person spot-check of `rbi_alert_list.csv` against the PDF — A

## Changelog

- 23 Oct 18:07 — Goal 2 started and stopped before any code (prerequisites missing, folder not a git repo). Plan set: Goal 0, then Goal 1, then Goal 2. Environment noted: Python 3.14.6 (stack says 3.11), Node 24.19, npm 11.17. No checklist items changed.
- 23 Oct 23:20 — Registries complete: BSE equity (5120), SEBI brokers (5002), advisers (1062), research analysts (2324) added via `scripts/fetch_sebi.py`; SOURCES.md has no manual-download rows left. SEBI/BSE blocker removed; commit-or-ignore decision on SEBI CSVs opened.
- 23 Oct 23:15 — Prerequisites: Tesseract 5.4 (eng, hin, osd), NSE equity CSV, RBI Alert List CSV (95), ReBIT AA schemas saved, SOURCES.md rows filled. SEBI and BSE lists blocked on manual download.
- 23 Oct 22:45 — Project docs and agent orchestration created.
