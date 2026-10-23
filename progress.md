# Kasauti — Progress

> Maintained by the `progress-keeper` agent. Humans may edit; keep the section headings.

## Status

| | |
|---|---|
| Phase | 2 · Video + evidence (UI flow done; video and evidence open) |
| Overall | 42% |
| Demo-ready | No |
| Last updated | 24 Oct 2026, 01:21 IST |

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
  - [x] Regex patterns
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
- [x] Noto Sans Devanagari font (bundled via `@fontsource/noto-sans-devanagari`; the offline run made 0 non-localhost requests)
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
- [ ] Deck fixes: "NSDL to be confirmed" (Pitch 7, Arch 3); fraud figure to ₹22,495 crore / "over 75%" (Pitch 2); drop "and lips" (Pitch 6); Pitch 4 Hindi sentence names only CDSL; Pitch 10 "real public lists" for payee check (@valid and Suspect Registry are mocks); demo broker is now Zyphra Stock Club
- [ ] Verify or drop: Supreme Court hash ruling, Singapore 2,700+, FBI 77%, face-swap attribution paper, CBI ABHAY
- [ ] Q&A answers: "isn't this just a lookup?", "fully AI-generated video?", "why would a victim share a screenshot?"

**Logistics**
- [ ] Laptops, chargers, extension board, HDMI/USB-C adapters, a phone, mobile hotspot, college ID

## Phase checklist

### Phase 0 · Setup (hours 0–4)
- [x] Repo docs: CLAUDE.md, README.md, PRD.md, progress.md
- [x] Agent orchestration config (.claude/)
- [ ] Repo on GitHub, everyone can push
- [x] Shared schemas frozen: `claims.py`, `verdict.py`, `evidence.py` (C)
  - Pydantic models match `docs/formats`; `test_schemas_agree` checks it
- [ ] Backend skeleton with stub routes returning sample data (C)
- [x] Frontend skeleton with `/app` and `/reviewer` routes (D)
- [x] SEBI, RBI, NSE, BSE lists downloaded and cached as CSV (A)
  - [x] RBI Alert List, NSE equity list
  - [x] SEBI intermediaries (brokers, advisers, research analysts), BSE equity list
  - [x] Decide whether SEBI CSVs are committed: git-ignore `data/registries/*.csv` except `rbi_alert_list.csv` (see Decisions log)
- [ ] Decide LLM provider (Bedrock Nova vs Claude) and log below (B)
  - No API key in `.env` yet; the demo cache was produced by the offline reader; `bedrock` and `anthropic` providers are not built
- [x] `.env.example`, `.gitignore`, requirements.txt, package.json

**Checkpoint:** every service returns sample data end to end.

### Phase 1 · Core slice (hours 4–16)
- [x] Synthetic portfolios generator, ReBIT format, incl. partial-coverage cases (A)
- [ ] Fake trading app screens + 60 screenshots, 6 layouts (A)
- [x] Claim reader + cache mode + schema validation (B)
  - `cache` and `offline` providers built; hosted providers (`bedrock`, `anthropic`) not built
- [x] AA mock, SEBI, UPI, RBI, Suspect Registry connectors (C)
- [x] Holdings comparator + verdict rules with full-coverage rule (C)
- [x] EN/HI templates (D)
- [x] Result screen (D)

**Checkpoint (reached 24 Oct):** screenshot in → "0 of 3 found" out. `demo-001` through `POST /api/check` for SYN-C0001, 0.78 s.

### Phase 2 · Video + evidence (hours 16–28)
- [ ] Consented "official" footage + 30 fakes with compression/crop variants (A)
- [ ] Footage index (pHash + embeddings) (B)
- [ ] Source matcher + transcript diff with time ranges (B)
- [ ] Evidence hash chain + `verify_chain()` + pack export (C)
- [x] Response actions: 1930 pre-fill, contact, callback (D)
  - Trusted contact and callback are MOCK, logged to `data/runtime/events.jsonl`
- [x] Full flow wired: share → confirm → consent → result → act (lead)

**Checkpoint (partly reached 24 Oct):** UI flow runs end to end on demo-001 (EN, HI, offline); video and evidence items still open.

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
| Rule correctness (300) | 100% | 300/300 (1261 holding claims) |
| Source match top-1 (30) | ≥ 90% | — |
| Adversarial | 0 false MATCHES | — |
| Comprehension | 5 / 5 | — |
| Result after consent | < 60 s | 0.78 s (demo-001, local) |
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
| 24 Oct | Demo broker renamed to "Zyphra Stock Club" | The original demo name is one typo from a registered SEBI firm, so it can't be CONTRADICTS under the rules. GOALS.md, README.md and PRD.md now use Zyphra Stock Club; the deck still needs the same change |
| 24 Oct | New reason code `BROKER_REG_NO_MISMATCH` (CONTRADICTS) | A claimed SEBI reg no must belong to the claimed name. FR-5 "exact name or reg no" would MATCH a borrowed registration number, the classic impersonation. Close-but-not-exact names on the reg no give NO_RECORD |
| 24 Oct | Non-exact broker names at similarity 0.9 or above are NO_RECORD (ambiguous) | FR-5 defines only 0.6–0.9, and MATCHES needs the exact normalised name |
| 24 Oct | `aa_mock` returns only the Summary section | Profile (PAN, mobile) and Transactions are never in the payload |
| 24 Oct | Broker match = exact normalised name (legal words dropped) -> MATCHES; distinctive words within one typo (insert, delete, substitute, adjacent swap) of a registered firm -> NO_RECORD; otherwise CONTRADICTS. Replaces the 0.6 difflib and 0.9 Jaro-Winkler ideas | One wrong letter in a short name is over 10% of it, so no similarity ratio could separate typos from invented names. Exact match keeps generic words, so "Zerodha Wealth Club" is never MATCHES (it is NO_RECORD). Generic-word list in backend/app/constants.py. PRD FR-5 broker row updated |
| 24 Oct | Reason code renamed `BROKER_NEAR_MATCH_AMBIGUOUS` -> `BROKER_NEAR_MATCH` (`docs/formats/verdict.schema.json` changed) | One code for one situation instead of two overlapping ones; the message now names the registered firm and reg no so the customer can check it on SEBI Check |
| 24 Oct | Ambiguous share names map to no ISIN | 289 of the 358 ambiguous names are mutual-fund ETFs whose BSE issuer_name is the fund house (e.g. "Aditya Birla Sun Life Mutual Fund" covers many ETFs); the rest are partly-paid or old/new ISINs of the same company. Picking one ISIN could produce a false CONTRADICTS |
| 24 Oct | Money shows with ₹ ("₹3.98 crore", "₹1,07,000"), not "Rs" | CLAUDE.md convention; the goal text said "Rs 3.98 crore" |
| 24 Oct | Message templates are bundled into the frontend from backend/app/templates (vite fs.allow '..') | One source for every sentence, works offline, no extra endpoint |
| 24 Oct | BSE candidates are labelled with the scrip name, not the issuer | For ETFs the issuer is the fund house, so all 11 Aditya Birla ETFs showed the same name |
| 24 Oct | demo-002 shows no payee | A MATCHES payee needs a SEBI @valid handle; inventing one for a real broker was avoided, so the genuine-investor screenshot has holdings and a real broker name only |

## Blockers

- ~~SEBI intermediaries and BSE equity list need manual download~~ Resolved 23 Oct: both fetched and logged in `data/SOURCES.md`.
- ~~Decision pending: SEBI CSVs in git or not~~ Resolved 23 Oct: git-ignored, see Decisions log.
- Tesseract is not on PATH. Code must read the install path from config/env (`C:\Program Files\Tesseract-OCR`) or PATH must be set on each laptop.
- ~~Goal 1 next: Pydantic models must match `docs/formats`; `demo-001` not yet made.~~ Resolved 24 Oct.
- ~~Risk: broker similarity uses difflib over whole normalised names, so generic words push made-up names into "ambiguous".~~ Resolved 24 Oct 00:13: one-typo rule.
- ~~Broker-matching goal stopped on its own stop rule (24 Oct, 00:10): no similarity metric separated invented names from one-letter typos.~~ Resolved 24 Oct 00:13: one-typo rule, see Decisions log.
- Environment note: Python on this laptop is 3.14.6, but the stack specifies 3.11. Node is 24.19 and npm is 11.17. Python Playwright 1.64 needed chromium-headless-shell build 1248, now installed.
- ~~Risk (not built): an ambiguous share name gives `HOLDING_ISIN_UNMAPPED` with unclear text.~~ Addressed 24 Oct: the UI offers an ISIN picker, and `HOLDING_NAME_AMBIGUOUS` is used when the customer skips the choice.
- ~~The FR-8.4 MATCHES-only and NO_RECORD-only screens are not yet driven in the browser.~~ Resolved 24 Oct 01:21: demo-002 and demo-003 passed in EN and HI.
- ~~The running dev backend predates the scrip-name label change.~~ Resolved 24 Oct 01:21: backend restarted in cache mode; /api/isin/candidates gives 11 distinct labels.
- The Hindi UI strings (71 in the `ui` section) need a fluent reader, like the verdict templates.

## Next up

1. Goal 3: video source check (footage index, source matcher, transcript diff) — lead / B
2. Hindi templates and UI strings to a fluent Hindi reader — D
3. Decide the LLM provider and add a key, or keep offline — B
4. Push the repo to GitHub and add all four members — Aryan

## Changelog

- 24 Oct 01:21 — Samples demo-002/003, reader fix, settings fix (commits fdf953d, 08a3103, dd46ae6, 502524f). `.claude/settings.json` deny rules now name the real secret files (.env, .env.local, .env.production, .env.development, .env.test) instead of `.env.*`, so .env.example is readable; .env.development and .env.test were added beyond the request so they stay blocked. The earlier "`.env.example` does not exist" note was wrong (the deny rule `Read(./.env.*)` blocked reads; the file is tracked), so the Phase 0 item is ticked and that blocker removed. Backend restarted in cache mode; /api/isin/candidates gives 11 distinct labels for the Aditya Birla ETFs. New samples from the same render script and offline reader (cache never hand-written; demo-001 PNG hash unchanged): demo-002 = SYN-C0028 (real case P0028), 4 holdings plus broker ZERODHA BROKING LIMITED, all MATCHES; demo-003 = SYN-C0025 (P0025, NSDL failed), 3 holdings, all NO_RECORD HOLDING_PARTIAL_COVERAGE, summary INCOMPLETE. `data/demo_cache/demo_customers.json` maps each sample to its customer; the frontend MOCK login takes ?customer=SYN-Cnnnn. Reader fix found while making demo-002: Tesseract read "22,54 ,831"; the offline parser now joins a digit group split by a space before the comma, with a test (without it one holding was silently dropped). Playwright: demo-002 and demo-003 in EN and HI all PASSED, with FR-8.4 checks driven by the template texts. MATCHES: confirmation, no alert, no complaint/trusted contact/callback. NO_RECORD: "We could not verify this", three self-checks, optional callback, no complaint. demo-001 offline regression PASSED. Screenshots: docs/screens/*_demo-002_*.png and *_demo-003_*.png. pytest 60 passed, ruff clean, 300/300, frontend build/lint/test (4 pass) clean. Overall 39% to 42% (14 of 33 top-level checklist items).

- 24 Oct 01:02 — Goal 2 done (bank app and result screen; commits 007adc5, b734a42, 7a6cd04, c82295b). `frontend/`: React + Vite + TypeScript + Tailwind; /api is proxied to :8000. /app runs share (screenshot; a video is hashed in the browser and becomes an endorsement claim) -> editable claim list -> MOCK AA consent with OTP -> two-column result -> actions. /reviewer is a placeholder. Every sentence comes from messages_en/hi.json (a new "ui" section, 71 strings, 0 missing in each language); a TypeScript-AST test fails on planted hard-coded sentences (6 kinds). New endpoints: GET /api/isin/candidates and POST /api/events (trusted contact and callback are MOCK, logged to data/runtime/events.jsonl, git-ignored). New reason code HOLDING_NAME_AMBIGUOUS, used when the customer skips the ISIN choice; only rules.holding gained that branch. Playwright (Python, installed Chromium) ran demo-001 in EN and HI, then again offline (non-localhost blocked, backend LLM_PROVIDER=cache): all PASSED; screenshots in docs/screens/; no empty glyph boxes in Hindi; the offline run made 0 non-localhost requests. Ambiguous-name picker checked in the browser: 11 candidate ISINs plus "I am not sure"; Continue stays disabled until a choice. pytest 54 passed, ruff clean, frontend build/lint/test (4 pass) clean, 300/300 portfolios. Ticked: frontend skeleton, result screen, response actions, full flow wired, Noto Sans Devanagari font (bundled via @fontsource/noto-sans-devanagari). Not ticked: `.env.example` is missing, so that Phase 0 item stays open. Video, footage, source matcher, evidence chain and reviewer console untouched. Three decisions and three open items logged.
- 23 Oct 22:45 to 24 Oct 00:21 (Phases 0-1, folded) — Docs and agent config created; prerequisites fetched (Tesseract 5.4, NSE/BSE, SEBI lists, RBI Alert List, ReBIT schemas, SOURCES.md). Goal 0: git repo, `docs/formats` (4 schemas, validated 4/4), EN/HI templates for all reason codes, 300 synthetic portfolios, 6194-row ledger plus 79-entry mock Suspect Registry, backend skeleton. Goal 1: `demo-001` through `POST /api/check` for SYN-C0001 in 0.78 s (0 of 3 holdings found), image-injection test passes, grep test finds no "safe", "verified", "genuine" or "%". Broker matching: first Jaro-Winkler attempt stopped on its own rule (86% vs 90% target), then replaced by the one-typo rule (invented 50/50 CONTRADICTS, typos 50/50 NO_RECORD, 0 false MATCHES). `BROKER_NEAR_MATCH` now names the closest registered firm and reg no; ISIN normaliser covers all NSE series; 358 ambiguous names map to no ISIN, 0 map wrongly. Single ruff config. pytest 51 passed at that point.
