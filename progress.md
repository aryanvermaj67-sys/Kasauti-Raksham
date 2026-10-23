# Kasauti — Progress

> Maintained by the `progress-keeper` agent. Humans may edit; keep the section headings.

## Status

| | |
|---|---|
| Phase | 0 · Setup |
| Overall | 15% |
| Demo-ready | No |
| Last updated | 23 Oct 2026, 23:48 IST |

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
  - `scripts/fetch_registries.py` marks it "manual download needed"; expected path is `docs/sources/sahamati_fi_types_screenshot.png`

**Offline kit**
- [ ] CLIP or DINOv2 weights + imagehash
- [ ] `pip download -r requirements.txt -d wheels/`, npm cache, Docker images if used
- [ ] Noto Sans Devanagari font
- [ ] Pen drive with all of the above + backup demo video

**Media and synthetic data**
- [ ] Signed consent forms from every teammate on camera or voice
- [ ] 5–10 "official" speech videos + manipulated versions + compressed/cropped copies (30-video test)
- [ ] ~60 fake-app screenshots, 6 layouts, Hindi + English
- [x] ~300 synthetic portfolios (fake, mixed, real, no demat, partial coverage)
- [x] Synthetic payments ledger with scam pattern + mock Suspect Registry
- [ ] Frozen test set written by someone else, hashed

**Design**
- [x] JSON formats frozen: claims, verdicts, record responses, evidence pack
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
  - [x] Decide whether SEBI CSVs are committed: git-ignore `data/registries/*.csv` except `rbi_alert_list.csv` (see Decisions log)
- [ ] Decide LLM provider (Bedrock Nova vs Claude) and log below (B)
- [ ] `.env.example`, `.gitignore`, requirements.txt, package.json

**Checkpoint:** every service returns sample data end to end.

### Phase 1 · Core slice (hours 4–16)
- [x] Synthetic portfolios generator, ReBIT format, incl. partial-coverage cases (A)
- [ ] Fake trading app screens + 60 screenshots, 6 layouts (A)
- [ ] Claim reader + cache mode + schema validation (B)
- [ ] AA mock, SEBI, UPI, RBI, Suspect Registry connectors (C)
- [ ] Holdings comparator + verdict rules with full-coverage rule (C)
- [x] EN/HI templates (D)
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
| 23 Oct | RESOLVED (next rows): commit or git-ignore the SEBI CSVs | They total ~2 MB and hold public contact emails/phones; CLAUDE.md says not to commit large copies of public lists |
| 23 Oct | Run GOALS.md in order: Goal 0, then Goal 1, then Goal 2 | Goal 2 (bank app + result screen) was started but stopped before any code; its prerequisites do not exist yet |
| 23 Oct | Git-ignore `data/registries/*.csv` except `rbi_alert_list.csv` | RBI list is our own hand transcription. Public lists stay local; `scripts/fetch_registries.py` re-fetches or verifies them against SOURCES.md hashes |
| 23 Oct | `aa_mock` returns one RecordResponse per depository (source `aa_mock:CDSL` / `aa_mock:NSDL`) with status OK or FAILED | The full-coverage rule can see each depository separately |
| 23 Oct | Templates are two-column (app/record) per reason_code; money and depository lists are raw params | The UI formats them per language (Indian number format, {depositories}) |

## Blockers

- ~~SEBI intermediaries and BSE equity list need manual download~~ Resolved 23 Oct: both fetched and logged in `data/SOURCES.md`.
- ~~Decision pending: SEBI CSVs in git or not~~ Resolved 23 Oct: git-ignored, see Decisions log.
- Tesseract is not on PATH. Code must read the install path from config/env (`C:\Program Files\Tesseract-OCR`) or PATH must be set on each laptop.
- Goal 1 next: Pydantic models must match `docs/formats`; `demo-001` not yet made.
- Environment note: Python on this laptop is 3.14.6, but the stack specifies 3.11. Node is 24.19 and npm is 11.17.

## Next up

1. Run Goal 1 (backend slice) — lead
2. Hindi templates to a fluent Hindi reader — D
3. Take the Sahamati screenshot (`docs/sources/sahamati_fi_types_screenshot.png`) — A
4. Push the repo to GitHub and add all four members — Aryan

## Changelog

- 23 Oct 23:48 — Goal 0 done. Git repo initialised locally, 6 commits. `docs/formats/` has 4 JSON Schemas plus examples; `scripts/validate_formats.py` prints "validated 4/4 examples". Templates `messages_en.json` and `messages_hi.json` cover all 23 reason codes ("0 missing" in both); every Hindi entry is flagged needs_native_review, and holdings messages take {depositories} as a parameter. `gen_portfolios.py --n 300 --seed 42` writes 60 cases each of fake_app_only, mixed, real, no_demat, plus 60 partial_depository_failure (30 CDSL ok / NSDL failed, 30 the reverse); ReBIT equities v1.0.0 shape (transcribed in `data/schemas/rebit_equities_v1.0.0.schema.json`), deterministic. `gen_ledger.py` writes 6194 transactions with the scam pattern injected for 40 customers, plus a mock suspect registry of 79 entries. `fetch_registries.py` verifies 8 of 9 SOURCES.md files by SHA-256; Sahamati screenshot still needs a manual download. `backend/` has /health, requirements.txt, pytest and ruff config; pytest 6 passed, ruff clean. Duplicate root `bse_equity.csv` (same SHA-256 as `data/registries/`) removed; `.gitattributes` `data/** -text` keeps data hashes stable on Windows. SEBI CSV decision closed (git-ignored).
- 23 Oct 23:37 — Goal 2 started and stopped before any code (prerequisites missing, folder not a git repo). Time corrected from 18:07, which was UTC. Plan set: Goal 0, then Goal 1, then Goal 2. Environment noted: Python 3.14.6 (stack says 3.11), Node 24.19, npm 11.17. No checklist items changed.
- 23 Oct 23:20 — Registries complete: BSE equity (5120), SEBI brokers (5002), advisers (1062), research analysts (2324) added via `scripts/fetch_sebi.py`; SOURCES.md has no manual-download rows left. SEBI/BSE blocker removed; commit-or-ignore decision on SEBI CSVs opened.
- 23 Oct 23:15 — Prerequisites: Tesseract 5.4 (eng, hin, osd), NSE equity CSV, RBI Alert List CSV (95), ReBIT AA schemas saved, SOURCES.md rows filled. SEBI and BSE lists blocked on manual download.
- 23 Oct 22:45 — Project docs and agent orchestration created.
