# Kasauti — Progress

> Maintained by the `progress-keeper` agent. Humans may edit; keep the section headings.

## Status

| | |
|---|---|
| Phase | 5a · Demo hardening, on `main`. Frozen-set validation (no-video scope, set hash `d2bfe2f3…40ec`) run eight times; run 8: 274/274 outcomes, FALSE CONTRADICTION 0 (details in Test results, `docs/VALIDATION_SUMMARY.md`, `docs/VALIDATION_RUN8.md`). 60 MOCK fake-app screenshots made and scored (97.8% fields). Post-freeze rule and reader fixes, local commits ahead of origin/main, not pushed. Open: a009 needs a rerun through the video route once the real official clips are indexed, the 32 frozen clips and the consented-video evaluation (s01-s08), consented footage (user recording), comprehension test, Hindi review, Wi-Fi-off rehearsal, backup video |
| Overall | 70% (23 of 33; fake-app screenshot item done) |
| Demo-ready | No (scripted offline run and browser run of demo-001 pass; Wi-Fi not physically switched off, no backup video, no consented footage, video part of the frozen set not run, GPU memory tight with gemma kept loaded) |
| Last updated | 25 Oct 2026, 03:36 IST |

## Team and ownership

| Role | Owner | Area |
|---|---|---|
| A | _fill_ | Fake trading app, synthetic data, consented videos |
| B | _fill_ | Claim reader, video source finder |
| C | _fill_ | Backend: connectors, verdict rules, evidence chain |
| D | _fill_ | Bank app UI, reviewer console, pitch |

## Pre-finale checklist (before 24 Oct)

**Rules to confirm with organisers**
- [x] Pre-written code allowed, or only data, designs and models? Organisers confirmed pre-written code IS allowed; the form was submitted (25 Oct)
- [ ] Venue internet, power, paid cloud APIs allowed?
- [ ] Registered track matches the deck (Track 03)

**Accounts and keys (test on a fresh laptop)**
- [x] Local reader: EasyOCR (hi+en) + Ollama `gemma3:4b` (fallback `qwen2.5:3b`); models must be on the pen drive (`docs/SETUP_LOCAL_MODELS.md`)
- [ ] Offline fallback: Tesseract + Hindi pack + regex patterns
  - [x] Tesseract 5.4 installed at `C:\Program Files\Tesseract-OCR` with eng, hin (tessdata_fast), osd; not on PATH (set path in config); regex patterns done
- [x] Whisper weights and ffmpeg installed (faster-whisper small in `models/whisper`; ffmpeg 9.0.2)

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
- [x] CLIP weights + imagehash (open_clip ViT-B/32 laion2b; weights in `models/`, git-ignored)
- [ ] `pip download -r requirements.txt -d wheels/`, npm cache, Docker images if used
  - [x] pip: `wheels/` 277 MB, 67 files (CPU torch), git-ignored; a fresh clone installed the video wheels `--no-index` from it
  - [ ] npm cache: steps documented in README, `npm --offline` install not tested
- [x] Noto Sans Devanagari font (bundled via `@fontsource/noto-sans-devanagari`; the offline run made 0 non-localhost requests)
- [ ] Pen drive with all of the above + backup demo video
  - [x] `scripts/make_kit.ps1` / `scripts/restore_kit.ps1`: kit of `models/`, `wheels/`, `data/media/`, `data/footage_index/`, `frontend/node_modules` (instead of the 3.5 GB npm cache), `.env`, the Ollama models folder and the EasyOCR folder, with a SHA-256 manifest; restore verifies every file before copying. Tested on a temp folder only: 1361 files, 6.61 GB, make 47 s, manifest OK, restore 40 s into a temp clone and temp home
  - [ ] Kit written to the real pen drive and restored on a second laptop; backup video not recorded
  - The kit holds `.env` with `EVIDENCE_KEY`: keep the drive with the team

**Media and synthetic data**
- [ ] Signed consent forms from every teammate on camera or voice
- [ ] 5–10 "official" speech videos + manipulated versions + compressed/cropped copies (30-video test)
- [x] ~60 fake-app screenshots, 6 layouts, Hindi + English
  - `scripts/make_fake_app_screens.py`: 60 MOCK screenshots (30 EN + 30 HI, 6 layouts) with exact labels in `data/media/fake_apps/` (git-ignored, regenerated from `--seed`); `--score` reads them through the real reader
- [x] ~300 synthetic portfolios (fake, mixed, real, no demat, partial coverage)
- [x] Synthetic payments ledger with scam pattern + mock Suspect Registry
- [ ] Frozen test set written by someone else, hashed
  - [x] Spec: `docs/FROZEN_SET_SPEC.md` (layout, minimum counts, author rules, HASH.txt recipe)
  - [x] Checker: `scripts/check_frozen.py` (structure, schemas, counts, coverage; writes HASH.txt once, then verifies); `data/frozen_example/` passes in `--example` mode
  - [x] `data/frozen/` authored to the spec by someone who does not write the verdict rules, in no-video scope
    - First version received 24 Oct (`frozen-set.zip`, sha256 `371eb0a3…e18a06`), committed as received in 835441d. The writer's later version with three `HOLDING_NO_CONSENT` cases is committed as dce03df and hashed in no-video scope (set hash `d2bfe2f3…40ec`)
    - The 32 clips in `videos/manifest.json` are still missing everywhere searched, so the full-scope hash does not exist; video items stay open
  - [x] No-video scope (committed d79017b, 9fc1396): `check_frozen.py --skip-videos`; `HASH.txt` first line `scope: no-video` is part of the hashed text and decides the scope for `check_frozen.py` and `run_frozen.py`. A full-scope hash cannot be weakened without `--rehash`; changed, added or removed files still refused. `run_frozen.py` lists manifest videos as "not run (no-video scope)". Spec section and 6 tests
  - [x] Runner `scripts/run_frozen.py`: refuses unless `check_frozen` passes incl. `HASH.txt`; never writes `data/frozen`. Now run six times on the real set in no-video scope (see Test results); model warmed first, name-mapped ISINs counted separately, security names compared like the app

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
- [x] Repo docs: project rules file, README.md, PRD.md, progress.md
- [x] Agent orchestration config
- [ ] Repo on GitHub, everyone can push
- [x] Shared schemas frozen: `claims.py`, `verdict.py`, `evidence.py` (C)
  - Pydantic models match `docs/formats`; `test_schemas_agree` checks it
- [ ] Backend skeleton with stub routes returning sample data (C)
- [x] Frontend skeleton with `/app` and `/reviewer` routes (D)
- [x] SEBI, RBI, NSE, BSE lists downloaded and cached as CSV (A)
  - [x] RBI Alert List, NSE equity list
  - [x] SEBI intermediaries (brokers, advisers, research analysts), BSE equity list
  - [x] Decide whether SEBI CSVs are committed: git-ignore `data/registries/*.csv` except `rbi_alert_list.csv` (see Decisions log)
- [x] Decide LLM provider and log below (B)
  - Decided 24 Oct: free local reader (`LLM_PROVIDER=local`, default); cloud providers removed; see Decisions log
- [x] `.env.example`, `.gitignore`, requirements.txt, package.json

**Checkpoint:** every service returns sample data end to end.

### Phase 1 · Core slice (hours 4–16)
- [x] Synthetic portfolios generator, ReBIT format, incl. partial-coverage cases (A)
- [x] Fake trading app screens + 60 screenshots, 6 layouts (A)
  - Reader score on them: 497/584 fields first pass (536 counting name-mapped ISINs), 571/584 (97.8%) after the reader fixes below (target ≥ 95%)
- [x] Claim reader + cache mode + schema validation (B)
  - `local` (default) and `offline` providers built (`reader/local.py`, `local_prompt.txt`); hosted providers removed. Local: one retry, then fallback to the Tesseract reader with `reader.fallback=true` in the evidence pack
  - Models compared on demo-001..003 (56 fields): gemma3:4b 56/56, 0 invented claims; qwen2.5:3b 49/56 on GPU, 53/56 on CPU. Speed ~4.5 s/image GPU, ~46 s CPU; gemma peaks at 7.1 GB VRAM with CLIP, Whisper and EasyOCR loaded (8.15 GB card)
  - `demo_cache` regenerated from the local reader; verdicts via the real API on local equal the cache-mode and old offline-cache verdicts for all three demos
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
  - [x] Rules part: `test_rules.py` already covers borrowed reg no, renamed broker/platform, lookalike payee, injected text
  - [ ] Unindexed / consented-video suite (needs the consented clips)
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
  - Clears evidence DB, dev key file, MOCK registry additions, trigger acks, event log, packs, video results; restores the registry seed from git. First run: evidence checks 28 to 0, reviewer queue 15 to 0, seed 79 kept; `tests/test_demo_reset.py` checks it
- [x] One-command demo run: `scripts/demo.sh` (GPU) / `scripts/demo.ps1` (`--cpu`), logic in `scripts/demo.py`
  - Resets, starts backend (`LLM_PROVIDER=cache`, `EVIDENCE_KEY` from `.env`, socket guard `scripts/offline_guard` blocks non-loopback connects) and frontend, waits for "video models ready", then runs demo-001 EN, HI, demo-002, demo-003, fake clip, reviewer approval: all PASSED, 0 blocked network attempts, printed "demo OK offline"
  - Open: Wi-Fi was not physically switched off; do it by hand at rehearsal
- [x] Fresh-clone test: after adding python-multipart to requirements.txt and copying bse_equity.csv by hand, 74 passed, 5 video tests skipped; with models/, data/footage_index/, data/media/ copied and wheels installed offline it worked. README lists the files to copy
- [x] Verdict-source test (`tests/test_verdict_source.py`): AST check that no backend module except `verdict/rules.py` builds a Verdict or hard-codes an outcome or reason code; runtime spy shows all 5 API verdicts came from `rules._v`; frontend never sets an outcome or reason code
- [x] MOCK footer in bank app and reviewer (EN/HI)
- [x] `docs/DEMO.md`: 3-minute script with on-screen text from the running app, fallback order (cache, offline reader, backup video), judges Q&A
- [x] Offline guards: `tests/test_offline_guard.py` (non-loopback IPv4 and IPv6 connections raise via `scripts/offline_guard`, loopback works); `demo.py` also sets `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `HTTP(S)_PROXY=http://127.0.0.1:9` (dead) with `NO_PROXY` for localhost; all 6 flows PASSED, "demo OK offline", 0 blocked attempts
- [x] Startup warm-up: backend loads CLIP, Whisper and (`LLM_PROVIDER=local`) EasyOCR + the Ollama model in a background thread; `/health` and `/api/health` return `ready=false` and the list still loading until done; a failed load is logged and no longer blocks. Bank app shows "preparing" (EN/HI template) with Check disabled until ready, verified in the browser by `demo.py`. Local backend ready after 48.1 s
- [x] `scripts/verify_all.sh` (`--quick`: pytest, ruff, templates, frontend build/lint/test, example frozen set; full adds `demo.py` and `run_frozen --example`); `--quick` run: ALL CHECKS PASSED
- [x] `scripts/measure_load.py`: memory and CPU-only measurements (see Test results)
- [x] Demo-day preflight: `scripts/preflight.py` / `preflight.ps1`, one line per check, prints GO or NO-GO with fixes
  - Checks: GPU free memory (4 GB before models load, 1.6 GB once `/health` is ready, from the measured 7181-5659=1522 MB concurrent headroom); Ollama with gemma3:4b and qwen2.5:3b; EasyOCR, CLIP and Whisper weights and footage index; `/health` ready; `EVIDENCE_KEY` valid Fernet; evidence DB empty; ports 8000/5173 free or serving; Noto Sans Devanagari bundled; git tree clean; commit hash
  - First run, servers down: NO-GO for `/health`, 7 stored checks, dirty tree; 7.7 GB GPU free. `tests/test_preflight.py`: a silent process holding a port is NO-GO
  - [x] Preflight GO: shown last session, GO on all 10 checks at commit bf048c1 (after the IPv6 port fix). Not re-run at 835441d; servers were down this session
- [x] `docs/DEMO_DAY.md`: start order, wait times (29-41 s cache mode, 47-48 s local mode), what to close, reset steps, GPU out-of-memory (`KASAUTI_LOCAL_MODEL=qwen2.5:3b`, CPU last resort), Ollama down (automatic offline fallback or `LLM_PROVIDER=offline`), network down (cache mode), Wi-Fi-off checklist
- [x] Example frozen set fixed (`data/frozen_example/`, example only): 1100 px PNGs with Arial / Nirmala UI; `ex_a1` label corrected (image makes no registration claim, so NO_RECORD `BROKER_NOT_FOUND_NOT_CLAIMED`); `ex_s1` total label set to 1,20,00,000 to match the image; re-hashed with `--rehash`, combined hash `f1c77f42c8e4e3d5f3a6ac5334ab16b679ae987d83a433f418c9f8c0ab9ddaca`
- [x] Reader hardening (B), committed in ff73c5d (not pushed): `local.py` OCR clean-up (Devanagari digits, ₹ read as र), number and UPI validators, prompt rules, tests, `scripts/make_dev_reader_set.py`, `scripts/eval_dev_reader.py`, `data/dev_reader/`. Fresh before/after eval on 24 dev images in `docs/READER_HARDENING_EVAL.md`
  - Improved: gemma3:4b broker names 5/7 -> 7/7, language 17/24 -> 20/24; total guard better
  - Regressed: payee claims are dropped when OCR garbles the UPI id (gemma3:4b total errors 66 -> 82, qwen2.5:3b 81 -> 75); gemma3:4b holding names/quantities slipped 2-3 fields. By design the customer re-adds the payee on the confirm screen. Needs a team decision (see Blockers)
- [x] UI design integration (D, lead), now on `main` (commits ceec7e4, ea38484, 47e5d98; `main` pushed at 20a1050)
  - The design export (untrusted prototype: mock data, Google Fonts and Material icons, outcome words like ALTERED / PARTIAL MATCH, real brands and a minister) was moved to `ui_incoming/` (git-ignored, never run); its `frontend/` duplicates were byte-identical and removed. Spec and two reference PNGs in `docs/design/reference/`; mapping in `docs/UI_INTEGRATION.md`
  - `/app`: 8 steps (Payment, Upload, Confirm, Consent, Checking, Result, Action, Pack), EN/HI from the templates, Inter + Noto Sans Devanagari bundled, lucide-react icons, spec tokens (4 px radius, tabular numerals, 44 px targets, 19 px large-text mode), `/api/health` chip ("Preparing" disables Check). Outcome labels: "MATCHES THE RECORD", "CONTRADICTS THE RECORD", "NO RECORD FOUND". Checking shows real call progress (no timers); Result shows each claim beside its records (source, fetched_at, MOCK/public); Pack downloads the real pack and shows the backend SHA-256 of the exact bytes; read-aloud only if a voice exists for the language
  - New endpoints: `GET /demo/scenarios`, `GET /demo/files/{name}` (whitelist, traversal 404), `GET /api/checks/{id}/records` and `/pack` (own customer only), `GET /cases` (New / In review / Approved / Rejected), `GET /stats` (outcome counts, median latency from the evidence store; latency now stored in the verdict entry; prompt rate computed live), `POST /demo/run` and `POST /demo/reset` (only with `KASAUTI_DEMO=1`). Reviewer detail adds a MOCK linked-accounts panel (Suspect Registry mock + ledger payers); Approve/Dismiss already write a review entry into the hash chain
  - `/reviewer` and `/present` rebuilt (EN/HI); `/present` shows phone and console as two pages that each poll the backend (no shared state), Run starts a real run, Reset calls `POST /demo/reset`. New reason code `HOLDING_NO_CONSENT` (post-freeze, see Decisions log)
- [x] Frozen-set validation, no-video scope (25 Oct): eight runs, run 1 251/274 outcomes with 14 false contradictions, run 8 274/274 with 0; post-freeze changes with tests in `test_post_freeze_rules.py` and `test_rules.py` (Decisions log). `docs/VALIDATION_SUMMARY.md`, `VALIDATION_RUN1..8.md`, `validation_results_run*.json`
  - [x] Reader fixes found by the fake-app set, with tests: UPI handle completed from the printed one, SEBI reg no taken from the page, platform category needs a text cue and the name is the app title, lost decimal points (7 68 लाख, 684 लाख), bare L/Cr amounts, grouped quantities (2 500), 'Lta' read for 'Ltd', total on the line after a stray rupee sign
  - [x] No-demat rule (`HOLDING_NO_DEMAT`) applied in PRD FR-5, EN/HI templates, `test_rules.py`, `scripts/gen_portfolios.py` and the 60 `no_demat` synthetic portfolios
  - [x] a009 (sourceless video frame) now scored through the video route: the harness makes a 3 s silent clip, calls `POST /api/video`, then the rules
  - [ ] Rerun a009 once the real official clips are indexed
  - [ ] Consented-video evaluation (s01-s08 clips, `make_test_clips.sh`): waiting for the clips and the script on this laptop
- [ ] Backup demo video recorded
- [ ] Physical Wi-Fi-off rehearsal
- [ ] `npm --offline` install tested

## Test results

| Test | Target | Result |
|---|---|---|
| Claim fields read | ≥ 95% | 60 MOCK fake-app screenshots (6 layouts, 30 EN + 30 HI, `make_fake_app_screens.py --score`, real reader): 497/584 first pass (536 counting name-mapped ISINs), 571/584 = 97.8% after fixes. Earlier: gemma3:4b 56/56 on demo-001..003 (0 invented claims); qwen2.5:3b 49/56 GPU, 53/56 CPU |
| Rule correctness (300) | 100% | 300/300 (1261 holding claims) |
| Source match top-1 (30) | ≥ 90% | 30/30 = 100% (dev clips, not the consented set) |
| Unindexed clips (sourceless) | NO_RECORD | 3/3 NO_RECORD; 0 misses returned MATCHES; slowest source search 1.23 s |
| Adversarial | 0 false MATCHES | Injection only so far: real-model tests in EN and HI, instruction text never becomes a claim and no verdict is MATCHES. Renamed broker, near-duplicate UPI and sourceless video suites still open |
| Comprehension | 5 / 5 | — |
| Result after consent | < 60 s | 0.78 s (demo-001, local) |
| Prompts per 1,000 customers | report | 133 on a clean registry (40 of 300 customers, one prompt per campaign); 40/40 prompted are injected scam-pattern customers, 0 others (synthetic ledger where the pattern was injected to fit the rule, so this is an upper bound). The live figure on `/stats` showed 150 after the e2e approval added a payee to the MOCK registry; labelled upper bound on a synthetic ledger |
| Source search < 5 s | < 5 s | GPU 2.17 s; CPU fallback (CUDA_VISIBLE_DEVICES=-1) 2.66 s |
| Full video result (read + video + check) < 60 s | < 60 s | GPU 11.50 s; CPU fallback 18.11 s |
| Offline demo run (`scripts/demo.py`) | all steps pass | 24 Oct 12:53: all 6 flows PASSED, "demo OK offline", 0 blocked attempts under the socket guard plus HF/transformers offline vars and a dead proxy (Wi-Fi not physically off). Earlier run (05:30) was reported as 7 steps |
| Full suite | green | 25 Oct, after run 8: backend pytest 156 passed, ruff clean (as reported by the lead). After run 7: 151 passed. Earlier the same day, 148 passed and `scripts/verify_all.sh --quick` ALL CHECKS PASSED. Earlier, 24 Oct at ff73c5d: pytest 119, frontend 7 tests + typecheck + build OK, real-model injection tests EN and HI |
| Reader hardening eval (24 dev images) | report | `docs/READER_HARDENING_EVAL.md`: gemma3:4b broker names 5/7 -> 7/7, language 17/24 -> 20/24; total errors worse (gemma3:4b 66 -> 82, qwen2.5:3b 81 -> 75) because payees are dropped when OCR garbles the UPI id; gemma3:4b holding names/quantities slipped 2-3 fields. Dev images, not the frozen set |
| Browser run, demo-001 (24 Oct evening) | all steps | Read, confirm, consent, check, result through the Vite UI (proxy to :8000 already wired) incl. the video step: "original video exists, words changed at 0:11-0:13". An earlier NO_SOURCE result came from another session's reset clearing results |
| Frozen set, real `data/frozen/`, no-video scope (25 Oct, run 1 to run 8) | report | Not a full-scope result: the 32 video clips were not run. Run 8 (latest): outcomes 274/274; FALSE CONTRADICTION 0; reason codes 307/307; screenshot fields 607/632; reader fallbacks 0; injection 5/5 (run 7: fields 603/632, read time 1.9-7.0 s per screenshot on GPU). Run 1 (before fixes) was 251/274 outcomes with 14 false contradictions and 372/632 fields. a009 is now scored through the video route (sourceless frame, 3 s silent clip), so it must be rerun when the real official clips are indexed. 25 screenshot fields still wrong from OCR limits (run 8). Earlier CPU subset: 21-83 s per screenshot; prompt rate 133 per 1,000 (upper bound, synthetic ledger). `docs/VALIDATION_RUN8.md` |
| Frozen runner on `data/frozen_example/` (`--example`) | report | 24 Oct 13:13: outcomes 8/8, FALSE CONTRADICTION 0, reason codes 10/10, injection 1/1, fallbacks 0, screenshot fields 5/8 (3 real reader errors, labels unchanged). Example set only |
| Peak memory, image (local reader, gemma3:4b) + video request at once | < 7.8 GB VRAM | 7181 MB peak on the whole GPU (includes 3740 MB already in use before start). Image 7.56 s, video 10.30 s concurrently |
| Local read, GPU hidden (backend `CUDA_VISIBLE_DEVICES=-1`, Ollama `num_gpu=0`) | < 60 s | demo-001 42.21 s, demo-002 44.65 s, demo-003 40.21 s per image, gemma3:4b, no fallback. Read alone is 40-45 s, so little margin on a CPU-only laptop in local mode |
| UI screenshots (`scripts/ui_screens.py`) | 0 blocked, 0 missing glyphs | 52 screenshots in `docs/screens/ui` (8 steps x EN/HI x 3 scenarios + reviewer and present EN/HI); 0 blocked non-localhost requests; 0 missing-glyph boxes on 25 Hindi screens. `scripts/demo.py` runs it: "demo OK offline" |

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
| 24 Oct | Message templates are bundled into the frontend from backend/app/templates (vite fs.allow '..') | One source for every sentence, works offline, no extra endpoint |
| 24 Oct | BSE candidates are labelled with the scrip name, not the issuer | For ETFs the issuer is the fund house, so all 11 Aditya Birla ETFs showed the same name |
| 24 Oct | demo-002 shows no payee | A MATCHES payee needs a SEBI @valid handle; inventing one for a real broker was avoided, so the genuine-investor screenshot has holdings and a real broker name only |
| 24 Oct | Index official frames also as 90% centre crops; frame cosine threshold 0.96 | CLIP alone could not tell a cropped copy from a look-alike slide; with crops indexed, cropped fakes reach 0.95+ while unindexed clips peak at 0.945 |
| 24 Oct | A campaign = trigger hits within 14 days of its first hit | Scams rotate new payee handles; counting each handle as a campaign gave 5.5 prompts per scam customer (220 total) against 1 now (40) |
| 24 Oct | Reviewer role comes from a MOCK X-Role header | No login in the prototype; the backend still refuses evidence to any non-reviewer role |
| 24 Oct | Demo reset restores the registry seed from git and generates `EVIDENCE_KEY` into `.env` if missing | Every rehearsal starts from the same state; `.env` had no key, one was generated (git-ignored) |
| 24 Oct | Demo run blocks non-loopback connects with a socket guard (`scripts/offline_guard`) | Gives a printed count of blocked network attempts as offline evidence until the Wi-Fi is switched off by hand |
| 24 Oct | A test enforces that only `verdict/rules.py` builds verdicts | Backs the "rules decide, never the LLM" rule with an AST check and a runtime spy |
| 24 Oct | `scripts/check_frozen.py` writes `HASH.txt` only when it is absent and all checks pass (or with `--rehash`); otherwise it verifies and fails on any changed, added or removed file | The goal said to write HASH.txt when everything passes, but rewriting it on every pass would hide tampering |
| 24 Oct | Frozen-set checker never reads or runs `verdict/rules.py`; labels are written by hand to `docs/FROZEN_SET_SPEC.md` | Keeps the frozen set independent of the rule author (a test checks the checker does not reference rules.py) |
| 24 Oct | Git-ignore `data/frozen/videos/*` except `manifest.json`; clips travel by pen drive | Video is large and project rules bar large media in git; the hash still covers the clips |
| 24 Oct | Claim reader is free and local: `LLM_PROVIDER=local` default (EasyOCR hi+en -> Ollama `gemma3:4b`, fallback `qwen2.5:3b` -> schema-validated ClaimSet; one retry, then the Tesseract reader with `reader.fallback=true` in the pack). Provider enum is now `local` / `offline`; cloud providers and API-key mentions removed from code, README, PRD, `.env.example`, project rules. Supersedes the 23 Oct hosted-vs-local plan | No key, no credits, nothing needed from the network at the venue |
| 24 Oct | gemma3:4b chosen over qwen2.5:3b as the default reader | 56/56 fields and 0 invented claims on demo-001..003 against 49/56 (GPU) and 53/56 (CPU) |
| 24 Oct | python-bidi pinned to 0.4.2 (pure Python) | The 0.6 DLL is blocked by Windows Application Control on this laptop |
| 24 Oct | `scripts/run_frozen.py` refuses to run unless `check_frozen` passes incl. `HASH.txt`, and never writes `data/frozen` | A result against a changed or unhashed set would mean nothing; tampered `payees.json` gives REFUSED, exit 2 (tested) |
| 24 Oct | Warm-up runs in a background thread; a failed load is logged and does not block; `ready=false` until done and the bank app disables Check ("preparing") | A first request must not hit cold models; one broken model should not take the backend down |
| 24 Oct | No `qwen2.5:3b` fallback added for memory pressure | Image + video together peaked at 7181 MB (whole GPU, incl. 3740 MB already used), under 7.8 GB; the existing fallback still covers only a missing model |
| 24 Oct | Frozen set committed as received (835441d); validation phases B and C skipped | The goal's rule: they run only if `check_frozen` passes, and it failed (32 clips missing). Nothing under `data/frozen` was edited; no `HASH.txt` written |
| 24 Oct | Reader total guard left unchanged (open for the team) | `tests/test_total_guard.py`: for an ad whose ₹99 crore total disagrees with its lines (₹3.98 crore) the reader nulls the total. Verdicts and the summary code (`HOLDINGS_TOTAL_NONE_FOUND`) are identical with and without the guard; only the shown claimed value changes (sum of lines, not the ad's ₹99 crore). No record checks totals, so no contradiction is hidden, but the ad's internal inconsistency, itself a red flag, is hidden from the customer. Decision for the team |
| 24 Oct | POST-FREEZE CHANGE: new reason code `HOLDING_NO_CONSENT` (NO_RECORD) when the customer refuses consent (`consent_scope` []); no holdings summary is shown then | The old path gave `HOLDING_PARTIAL_COVERAGE` with the false text "CDSL and NSDL could not be checked". Test in `test_ui_api.py`: a refusal never CONTRADICTS a holding. Consequence: the frozen set has no case for this code, so `check_frozen` coverage now also lists it (on top of the 32 missing clips); the frozen set was not edited |
| 24 Oct | The UI design export is untrusted: kept in `ui_incoming/` (git-ignored, never run); only the spec, two reference PNGs and the layout were taken, and every screen reads the real pipeline | The prototype used mock data, Google Fonts / Material icons, outcome words like ALTERED / PARTIAL MATCH, real brands and a minister; the project allows three outcomes, bundled fonts, no real people. Mapping in `docs/UI_INTEGRATION.md` |
| 24 Oct | `/demo/run` and `/demo/reset` work only with `KASAUTI_DEMO=1`; `/demo/files/{name}` is a whitelist; record and pack endpoints serve the customer's own checks only | Demo controls and file serving must not be reachable in a normal run |
| 25 Oct | The no-video scope for the frozen set is a documented, hashed scope, not a way around the hash: `HASH.txt` first line `scope: no-video` is part of the hashed text, a full-scope hash cannot be weakened without `--rehash`, and numbers from a no-video run say so at the top of the report | Lets validation run on screenshots, rule cases, brokers and payees while the 32 clips are missing, without letting anyone drop files or loosen a hash unnoticed. Resolves the "validate without videos needs a checker change logged as a decision" option in Blockers |
| 25 Oct | POST-FREEZE CHANGES, rules (tests in `backend/tests/test_post_freeze_rules.py`, 23 tests): (1) a typo anywhere in a broker name, generic words included, is a near match (NO_RECORD); (2) Devanagari names are normalised as letters, not erased; (3) a reg number on nobody's entry falls back to name logic; (4) a bare name that longer listed names begin with is ambiguous; (5) an ISIN on neither list is NO_RECORD `HOLDING_ISIN_UNMAPPED`, checked before partial coverage | (1) removed 10 false contradictions; (2) erasing Devanagari gave an empty-string near match; (4) after a company split, a customer holding the other ISIN would be contradicted; (5) an OCR misread of an ISIN would read as 'not in your name'. Commits 9eaeb29, 823d4b5 and the next commit, not pushed |
| 25 Oct | POST-FREEZE CHANGES, reader: (6) OCR repairs for reg numbers (\|NZ), @ misread in handles, capital O inside a lower-case word; (7) ISIN check-digit repair of look-alike swaps, only to a listed ISIN; (8) Ollama keep_alive 60m, 1500-token cap, model layout of holdings list plus one broker/payee/platform; (9) Tesseract second reading for UPI handles and reg numbers; (10) grounding: null-words and page headings removed, 'registered' only if the text says so, an ISIN copied onto two holdings kept on one; (11) holdings that do not add up to the printed total get one retry, values filled from printed rupee amounts (L and Cr units), holdings in page order, payee created from a printed handle when the model returns none | gemma looped on empty claims until the 60 s limit and the model unloaded after 5 idle minutes; EasyOCR drops @; repairs only ever move to a listed value. Tests in `test_post_freeze_rules.py` and `test_local_reader.py` |
| 25 Oct | DECIDED (closes the OPEN row on rc-024, rc-025, rc-127): a customer with no demat account where every depository answered is CONTRADICTS, new reason code `HOLDING_NO_DEMAT`; if a depository failed it stays NO_RECORD. PRD FR-5, EN/HI templates, `test_rules.py`, `scripts/gen_portfolios.py` and the 60 `no_demat` synthetic portfolios updated | Matches the frozen labels, and the full-coverage rule still protects against a false contradiction: with every depository answering, no holding exists in the customer's name |
| 25 Oct | a009 (sourceless video frame) is scored through the video route: the harness makes a 3 s silent clip, calls `POST /api/video`, then applies the rules. Rerun when the real official clips are indexed | Endorsements come from video, not from a screenshot read, so a009 cannot be judged by the screenshot reader |
| 25 Oct | POST-FREEZE CHANGES, reader (run 7): values re-read off the page after the number check; ISIN recovered from page text; payee 'broker/advisor' set only if the text uses the word; adaptive 3x model timeout on CPU-only laptops (`KASAUTI_READ_TIMEOUT` overrides it); torch cache released after OCR | Fewer wrong values and invented roles; CPU-only laptops were timing out before the model finished; frees GPU memory for the model |
| 25 Oct | Pre-written code is allowed | Organisers confirmed it and the form was submitted; the existing codebase can be used at the finale |
| 25 Oct | POST-FREEZE CHANGES, reader (run 8, found by the 60 fake-app screenshots; tests added): UPI handle completed from the printed one; SEBI reg no taken from the page; platform category needs a text cue and the name is the app title, not a category line; lost decimal points repaired (7 68 लाख, 684 लाख); bare L/Cr amounts; grouped quantities (2 500); 'Lta' read for 'Ltd'; total on the line after a stray rupee sign | Reader score on the fake-app set rose from 497/584 to 571/584 (97.8%); frozen run 8 still 0 false contradictions. Fake-app screenshots are MOCK and regenerated from `--seed` |
| 24 Oct | OPEN, needs a team decision: keep reader hardening as committed (payee dropped when OCR garbles the UPI id; customer re-adds it on the confirm screen) or loosen the UPI validator | Fewer wrong payees reach the rules, but the hardening eval shows total errors up on gemma3:4b (66 -> 82) and 2-3 holding fields slipped; by design the confirm screen is the safety net |

## Blockers

- Tesseract is not on PATH. Code must read the install path from config/env (`C:\Program Files\Tesseract-OCR`) or PATH must be set on each laptop.
- Environment note: Python on this laptop is 3.14.6, but the stack specifies 3.11. Node is 24.19 and npm is 11.17. Python Playwright 1.64 needed chromium-headless-shell build 1248, now installed.
- ~~Validation waits for the writer's `HOLDING_NO_CONSENT` case~~ Resolved 25 Oct: the writer's version (dce03df) was hashed in no-video scope and validated six times. Still open: the 32 frozen clips (`data/frozen/videos/manifest.json`, none found), so no full-scope hash and the video part is not run; the consented-video evaluation (s01-s08, `make_test_clips.sh`) waits for the clips and the script on this laptop.
- GPU memory is tight with gemma kept loaded (a video source-search timing test took 8.7 s once under contention, passes alone). CPU-only reads exceed 60 s end to end (21-83 s on the frozen subset): a CPU-only demo laptop will miss the 60 s target.
- The Hindi UI strings (71 in the `ui` section, plus the new MOCK footer and "preparing" strings, and the new /app, /reviewer and /present strings) need a fluent reader, like the verdict templates.
- `data/registries/bse_equity.csv` cannot be fetched by script; a fresh clone needs it copied by hand (README lists it). Copy it onto the pen drive.
- The Wi-Fi-off rehearsal is not done: the offline proof so far is the socket guard (0 blocked attempts), not a physical disconnect.
- No backup demo video yet (last fallback in `docs/DEMO.md`).
- `npm --offline` install is untested; only the pip side of the offline kit is verified.
- Video: an off-centre 10% crop (top-left) matched only 35% of frames, so it gives NO_RECORD (a miss, never a false MATCHES). Consider multi-crop indexing or local features if the judges test this. All video results so far are on dev clips; re-run make/index/eval with the consented clips once forms are signed.
- The dev evidence key sits in `data/runtime/evidence.key` when `EVIDENCE_KEY` is unset. On this laptop `.env` now has an `EVIDENCE_KEY` (git-ignored); copy `.env` to the demo machine, otherwise the dev key file is used again.
- Local reader: Ollama and its models (`gemma3:4b`, `qwen2.5:3b`), EasyOCR weights must be on the demo machine; `make_kit.ps1` bundles them. Reader, reader hardening (ff73c5d, not pushed), validation runner, preflight, kit scripts and runbook are committed.
- To confirm: `docs/DEMO.md` and `scripts/demo.py` still describe `LLM_PROVIDER=cache`, while the provider enum is now `local` / `offline`; check which path the demo run uses.

## Next up

1. Push the local commits, rerun preflight on a clean commit; decide the reader-hardening payee trade-off — lead / Aryan
2. Record the official clips (user is recording), index them, rerun a009 through the video route, then the consented-video evaluation (s01-s08) and the full-scope hash with the 32 frozen clips — user / set's author / B
3. Teammates: Hindi review of templates (incl. new `HOLDING_NO_DEMAT`), comprehension test, deck fixes, role owners, Wi-Fi-off rehearsal, backup video — A / D

## Changelog

- 25 Oct 03:36 — Organisers confirmed pre-written code is allowed, form submitted (ticked, Decisions log). 60 MOCK fake-app screenshots done (`scripts/make_fake_app_screens.py`, 6 layouts, 30 EN + 30 HI, `--score`): reader 497/584 first pass, 571/584 (97.8%) after 8 reader fixes with tests. Frozen run 8 (no-video scope): 274/274 outcomes, 0 false contradictions, 307/307 reason codes, 607/632 fields, 0 fallbacks, injection 5/5; 156 backend tests pass, ruff clean. `docs/VALIDATION_SUMMARY.md`, `docs/VALIDATION_RUN8.md` updated. Lead reports a local commit, not pushed (git log at 03:36 still showed 18b7e73 on top). Overall 67% to 70% (23 of 33). Unchanged: consented video (user recording), Hindi review, comprehension test, deck fixes, role owners.
- 25 Oct 03:10 — Decision: no-demat customer with every depository answering is CONTRADICTS (`HOLDING_NO_DEMAT`), NO_RECORD if a depository failed; PRD FR-5, EN/HI templates, test_rules, gen_portfolios and 60 no_demat portfolios updated, rc-024/025/127 row closed. a009 now scored through the video route (rerun when the real clips are indexed). Reader fixes (re-read values, ISIN from page text, payee role wording, adaptive CPU timeout with `KASAUTI_READ_TIMEOUT`, torch cache release). Frozen run 7 (no-video scope): 274/274 outcomes, 0 false contradictions, 307/307 reason codes, 603/632 fields, 0 fallbacks, injection 5/5, read 1.9-7.0 s on GPU; 151 backend tests pass, ruff clean. Docs: `docs/VALIDATION_SUMMARY.md`, `docs/VALIDATION_RUN7.md`. Clips still pending (user recording). Not pushed. Overall stays 67%.
- 25 Oct 02:45 — Frozen-set validation, no-video scope, six runs (set hash `d2bfe2f3…40ec`): outcomes 251/274 to 270/274, FALSE CONTRADICTION 14 to 0, reason codes 306/307, screenshot fields 593/632, injection 5/5; 4 items left (3 label/PRD conflicts, 1 by design). 11 post-freeze changes logged with 23 tests; pytest 148 passed, ruff clean, `verify_all.sh --quick` passed. Video part and consented-video evaluation still waiting for clips. Not pushed. Earlier 25 Oct 00:12: no-video scope documented and committed (d79017b, 9fc1396, dce03df). Overall stays 67%.
- 24 Oct 11:17 to 16:05 (folded) — Frozen-set groundwork (spec, checker, runner, example set), free local claim reader (gemma3:4b 56/56 on demo-001..003, overall 64% to 67%), warm-up, offline guards, preflight, kit scripts, runbook; frozen set received and committed as received (835441d); new UI on the real pipeline (ceec7e4, ea38484, 47e5d98), `main` pushed at 20a1050; POST-FREEZE `HOLDING_NO_CONSENT`; reader hardening ff73c5d (payee trade-off open); browser run of demo-001 incl. video passed.
- 23 Oct 22:45 to 24 Oct 05:30 (folded) — Docs, prerequisites and synthetic data; Goal 1 slice (screenshot to "0 of 3 found" in 0.78 s); broker one-typo rule; bank app and result screen; video source check on dev clips (30/30 top-1); encrypted evidence chain, reviewer console, trigger rate (133 per 1,000); reset script, offline demo run, fresh-clone test, `test_verdict_source.py`, `docs/DEMO.md`. Overall 48% to 64% (21 of 33) by 05:30.

