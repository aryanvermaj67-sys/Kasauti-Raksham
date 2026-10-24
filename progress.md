# Kasauti — Progress

> Maintained by the `progress-keeper` agent. Humans may edit; keep the section headings.

## Status

| | |
|---|---|
| Phase | 5a · Demo hardening (reset, one-command offline demo run, fresh-clone test, offline kit for pip, demo script done; consented footage, adversarial suite, comprehension test, physical Wi-Fi-off rehearsal and backup video open) |
| Overall | 64% (21 of 33, same basis as before: Q&A answers and timing runs newly ticked) |
| Demo-ready | No (scripted offline run passes; Wi-Fi was not physically switched off, no backup video, no consented footage) |
| Last updated | 24 Oct 2026, 05:30 IST |

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
- [x] Whisper weights (small or medium) and ffmpeg installed
  - faster-whisper small in `models/whisper`; ffmpeg 9.0.2

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
- [x] CLIP or DINOv2 weights + imagehash
  - open_clip ViT-B/32 laion2b + imagehash; weights in `models/` (git-ignored)
- [ ] `pip download -r requirements.txt -d wheels/`, npm cache, Docker images if used
  - [x] pip: `wheels/` 277 MB, 67 files (CPU torch), git-ignored; a fresh clone installed the video wheels `--no-index` from it
  - [ ] npm cache: steps documented in README, `npm --offline` install not tested
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
- [x] Q&A answers: "isn't this just a lookup?", "fully AI-generated video?", "why would a victim share a screenshot?"
  - In `docs/DEMO.md` (judges Q&A section)

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
- [x] Footage index (pHash + embeddings) (B)
  - `scripts/build_footage_index.py`: 6 dev clips, 270 frames, 561 timed words, built offline from `models/`
- [x] Source matcher + transcript diff with time ranges (B)
  - `comparators/video.py`; `POST /api/video` stores a MOCK footage_index record; dev clips only, not the consented set
  - Open: consented footage item above stays unticked (no consented clips yet)
- [x] Evidence hash chain + `verify_chain()` + pack export (C)
  - `evidence/hashchain.py`, `evidence/pack.py`; JSON pack validates against `evidence_pack.schema.json`, plus an HTML listing that is not a legal certificate
- [x] Response actions: 1930 pre-fill, contact, callback (D)
  - Trusted contact and callback are MOCK, logged to `data/runtime/events.jsonl`
- [x] Full flow wired: share → confirm → consent → result → act (lead)

**Checkpoint (partly reached 24 Oct):** UI flow runs end to end on demo-001 (EN, HI, offline); the video path runs with demo-001 plus `dev_01_fake.mp4` (EN, HI, offline). Evidence chain done 24 Oct 02:24 (`scripts/e2e_review.py` PASSED). Consented footage still open.

### Phase 3 · Reviewer + validation (hours 28–40)
- [x] Reviewer console: queue, detail, approve/reject (D)
  - `/reviewer`, English only; approve adds the payee to the MOCK registry; a customer role gets 403
- [ ] Rule-correctness suite: 300 portfolios (C)
- [ ] Adversarial tests: injected text, renamed broker, near-duplicate UPI, sourceless video (B, C)
- [x] Timing runs vs targets (C)
  - GPU and CPU fallback both inside <5 s source search and <60 s result (see Test results); dev clips, local
- [x] Prompt-rate report on synthetic transactions (C)
  - `trigger.py`, `scripts/trigger_rate.py`; 133 prompts per 1,000 customers on the synthetic ledger (upper bound, see Blockers)
- [ ] Comprehension test with 5 adults (D)

**Checkpoint:** test results table + prompt rate ready.

### Phase 4 · Freeze (hours 40–48)
- [ ] Code freeze, tag `v1.0-demo`
- [ ] Offline run with `LLM_PROVIDER=cache`
- [ ] Backup demo video recorded
- [ ] Re-verify all cited figures in the deck
- [ ] Pitch rehearsal × 3, Q&A drill (sourceless video, false positives, consent)

### Phase 5a · Demo hardening
- [x] Reset script: `scripts/reset_demo.sh` / `.ps1` (logic in `backend/app/demo_reset.py`, `scripts/reset_demo.py`)
  - Clears evidence DB, dev key file, MOCK registry additions, trigger acks, event log, packs, video results; restores the registry seed from git if edited
  - First real run: evidence checks 28 to 0, reviewer queue 15 to 0, registry additions 1 to 0, events 14 to 0, dev key file 1 to 0, seed 79 kept
  - `tests/test_demo_reset.py` runs the full flow, then reset, and checks it is back to the seed
- [x] One-command demo run: `scripts/demo.sh` (GPU) / `scripts/demo.ps1` (`--cpu`), logic in `scripts/demo.py`
  - Resets, starts backend (`LLM_PROVIDER=cache`, `EVIDENCE_KEY` from `.env`, socket guard `scripts/offline_guard` blocks non-loopback connects) and frontend, waits for "video models ready", then runs demo-001 EN, HI, demo-002, demo-003, fake clip, reviewer approval: all PASSED, 0 blocked network attempts, printed "demo OK offline"
  - Open: Wi-Fi was not physically switched off; do it by hand at rehearsal
- [x] Fresh-clone test: after adding python-multipart to requirements.txt and copying bse_equity.csv by hand, 74 passed, 5 video tests skipped; with models/, data/footage_index/, data/media/ copied and wheels installed offline it worked. README lists the files to copy
- [x] Verdict-source test (`tests/test_verdict_source.py`): AST check that no backend module except `verdict/rules.py` builds a Verdict or hard-codes an outcome or reason code; runtime spy shows all 5 API verdicts came from `rules._v`; frontend never sets an outcome or reason code
- [x] MOCK footer in bank app and reviewer (EN/HI)
- [x] `docs/DEMO.md`: 3-minute script with on-screen text from the running app, fallback order (cache, offline reader, backup video), judges Q&A
- [ ] Backup demo video recorded
- [ ] Physical Wi-Fi-off rehearsal
- [ ] `npm --offline` install tested

## Test results

| Test | Target | Result |
|---|---|---|
| Claim fields read | ≥ 95% | — |
| Rule correctness (300) | 100% | 300/300 (1261 holding claims) |
| Source match top-1 (30) | ≥ 90% | 30/30 = 100% (dev clips, not the consented set) |
| Unindexed clips (sourceless) | NO_RECORD | 3/3 NO_RECORD; 0 misses returned MATCHES; slowest source search 1.23 s |
| Adversarial | 0 false MATCHES | — |
| Comprehension | 5 / 5 | — |
| Result after consent | < 60 s | 0.78 s (demo-001, local) |
| Prompts per 1,000 customers | report | 133 (40 of 300 customers, one prompt per campaign); 40/40 prompted are injected scam-pattern customers, 0 others (synthetic ledger where the pattern was injected to fit the rule, so this is an upper bound) |
| First /api/video after fresh start | report | 3.09 s (models preloaded, GPU) |
| Source search < 5 s | < 5 s | GPU 2.17 s; CPU fallback (CUDA_VISIBLE_DEVICES=-1) 2.66 s |
| Full video result (read + video + check) < 60 s | < 60 s | GPU 11.50 s; CPU fallback 18.11 s |
| Offline demo run (`scripts/demo.py`) | all steps pass | 7 steps PASSED, 0 blocked network attempts under the socket guard (Wi-Fi not physically off) |
| Full suite | green | pytest 83 passed; ruff, frontend build/lint/test clean; git log attribution grep = 0 |

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
| 24 Oct | Stretch items (detector score, C2PA) not built | Not needed for the demo; time went to making the source match trustworthy |
| 24 Oct | Index official frames also as 90% centre crops; frame cosine threshold 0.96 | CLIP alone could not tell a cropped copy from a look-alike slide; with crops indexed, cropped fakes reach 0.95+ while unindexed clips peak at 0.945 |
| 24 Oct | faster-whisper gets audio decoded by ffmpeg | its PyAV decoder breaks on the installed PyAV release |
| 24 Oct | A campaign = trigger hits within 14 days of its first hit | Scams rotate new payee handles; counting each handle as a campaign gave 5.5 prompts per scam customer (220 total) against 1 now (40) |
| 24 Oct | Reviewer role comes from a MOCK X-Role header | No login in the prototype; the backend still refuses evidence to any non-reviewer role |
| 24 Oct | Pack id = "pack-" + check id | Keeps the CheckResult format unchanged |
| 24 Oct | Demo reset restores the registry seed from git and generates `EVIDENCE_KEY` into `.env` if missing | Every rehearsal starts from the same state; `.env` had no key, one was generated (git-ignored) |
| 24 Oct | `hashchain._db` is a context manager that commits and closes | Connections were never closed and the SQLite file stayed locked on Windows (bug fixed) |
| 24 Oct | Demo run blocks non-loopback connects with a socket guard (`scripts/offline_guard`) | Gives a printed count of blocked network attempts as offline evidence until the Wi-Fi is switched off by hand |
| 24 Oct | A test enforces that only `verdict/rules.py` builds verdicts | Backs the "rules decide, never the LLM" rule with an AST check and a runtime spy |
| 24 Oct | python-multipart 0.0.32 added to requirements.txt | The fresh-clone test found it missing |

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
- The Hindi UI strings (71 in the `ui` section, plus the new MOCK footer string) need a fluent reader, like the verdict templates.
- `data/registries/bse_equity.csv` cannot be fetched by script; a fresh clone needs it copied by hand (README lists it). Copy it onto the pen drive.
- The Wi-Fi-off rehearsal is not done: the offline proof so far is the socket guard (0 blocked attempts), not a physical disconnect.
- No backup demo video yet (last fallback in `docs/DEMO.md`).
- `npm --offline` install is untested; only the pip side of the offline kit is verified.
- Video: an off-centre 10% crop (top-left) matched only 35% of frames, so it gives NO_RECORD (a miss, never a false MATCHES). Consider multi-crop indexing or local features if the judges test this.
- ~~Video: the first `/api/video` request loads the models (about 15 s).~~ Resolved 24 Oct 02:24: models preload at startup; first request 3.09 s.
- ~~Video: the complaint text does not yet mention the video finding.~~ Resolved 24 Oct 02:24: the 1930 complaint names the source clip, changed range and pack id (EN/HI test).
- The dev evidence key sits in `data/runtime/evidence.key` when `EVIDENCE_KEY` is unset. On this laptop `.env` now has an `EVIDENCE_KEY` (git-ignored); copy `.env` to the demo machine, otherwise the dev key file is used again.
- The reviewer UI is English only; its Hindi strings exist but are not toggled.
- The trigger rate comes from a synthetic ledger built to match the rule, so field precision is unknown.
- Video: all results are on dev clips. Re-run make/index/eval with the consented clips once the forms are signed.
- Environment note: an unrelated package (platformio) on this laptop pins click<8.4, and pip now has click 8.5.0. Not a Kasauti dependency.

## Next up

1. Physical Wi-Fi-off rehearsal of `scripts/demo.sh` / `demo.ps1`, then record the backup demo video; test `npm --offline` install — D / Aryan
2. Record consented official clips (after forms are signed) and re-run `scripts/video_eval.py`; adversarial suite (injected text, renamed broker, near-duplicate UPI, sourceless video) — A / B / C
3. Hindi templates and UI strings (incl. MOCK footer and the reviewer's Hindi toggle) to a fluent Hindi reader — D

## Changelog

- 24 Oct 05:30 — Phase 5a demo hardening. Reset script (`scripts/reset_demo.*`, `demo_reset.py`): first run took evidence checks 28 to 0, reviewer queue 15 to 0, registry additions 1 to 0, events 14 to 0, dev key file 1 to 0, seed 79 kept; `EVIDENCE_KEY` generated into `.env`; `test_demo_reset.py` covers flow then reset. Bug fixed: `hashchain._db` never closed SQLite connections (file locked on Windows), now a context manager. `scripts/demo.*`: reset, start backend (cache) and frontend under a socket guard, 7 steps (demo-001 EN/HI, demo-002, demo-003, fake clip, reviewer approval) all PASSED, 0 blocked network attempts, "demo OK offline"; Wi-Fi not physically switched off. Timing: source search GPU 2.17 s / CPU 2.66 s, full result GPU 11.50 s / CPU 18.11 s, both inside targets. Fresh clone: python-multipart was missing (added, 0.0.32), `bse_equity.csv` needs a manual copy; then 74 passed, 5 video tests skipped, and the clone's pip install worked offline from `wheels/` (277 MB, 67 files). `test_verdict_source.py` (AST + runtime spy: only `rules._v` makes verdicts; frontend sets none), MOCK footer in both UIs, `docs/DEMO.md` (script, fallback order, Q&A). pytest 83 passed; ruff and frontend build/lint/test clean; attribution grep 0. Ticked: Q&A answers, timing runs, pip wheels (sub-item). Overall 58% to 64% (21 of 33, same basis). Open: backup video, Wi-Fi-off rehearsal, `npm --offline`, Hindi footer review, consented footage, adversarial suite, comprehension test.
- 24 Oct 02:24 (Goal 4, folded; commits 5ae0575, 9a62440, 38a6c07) — Encrypted SHA-256 evidence chain per check with `verify_chain` (tampered ciphertext and hash both fail, tested), JSON/HTML evidence pack (not a legal certificate), reviewer console with MOCK X-Role (customer gets 403), FR-1.2 trigger rule (133 prompts per 1,000 customers, upper bound), models preloaded at startup (first /api/video 3.09 s), 1930 complaint names the video finding. `scripts/e2e_review.py` PASSED; pytest 79 passed. Overall 48% to 58% (19 of 33).
- 24 Oct 00:21 to 02:00 (Phase 2 so far, folded; commits 007adc5 to 5718061) — Bank app and result screen (React/Vite, /app flow, EN/HI strings from templates, offline Playwright runs), demo-002 and demo-003 samples, reader digit-group fix, settings deny-rule fix, and the video source check on dev clips (footage index, source matcher 30/30 top-1, unindexed 3/3 NO_RECORD, POST /api/video, CLIP and Whisper on GPU). Overall reached 48% (16 of 33) at that point.

- 23 Oct 22:45 to 24 Oct 00:21 (Phases 0-1, folded) — Docs and agent config created; prerequisites fetched (Tesseract 5.4, NSE/BSE, SEBI lists, RBI Alert List, ReBIT schemas, SOURCES.md). Goal 0: git repo, `docs/formats` (4 schemas, validated 4/4), EN/HI templates for all reason codes, 300 synthetic portfolios, 6194-row ledger plus 79-entry mock Suspect Registry, backend skeleton. Goal 1: `demo-001` through `POST /api/check` for SYN-C0001 in 0.78 s (0 of 3 holdings found), image-injection test passes, grep test finds no "safe", "verified", "genuine" or "%". Broker matching: first Jaro-Winkler attempt stopped on its own rule (86% vs 90% target), then replaced by the one-typo rule (invented 50/50 CONTRADICTS, typos 50/50 NO_RECORD, 0 false MATCHES). `BROKER_NEAR_MATCH` now names the closest registered firm and reg no; ISIN normaliser covers all NSE series; 358 ambiguous names map to no ISIN, 0 map wrongly. Single ruff config. pytest 51 passed at that point.
