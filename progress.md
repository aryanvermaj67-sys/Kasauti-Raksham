# Kasauti — Progress

> Maintained by the `progress-keeper` agent. Humans may edit; keep the section headings.

## Status

| | |
|---|---|
| Phase | 5a · Demo hardening (reset, offline demo run, fresh-clone test, frozen-set spec, checker and runner, free local claim reader, offline guards, warm-up, preflight (GO shown at bf048c1), kit scripts and runbook done; frozen set received and committed (835441d) but NOT OK: its 32 video clips are missing, so no `HASH.txt` and validation phases B and C were skipped; reader hardening uncommitted; consented footage, adversarial suite, comprehension test, Wi-Fi-off rehearsal and backup video open) |
| Overall | 67% (22 of 33, unchanged: the frozen set is a sub-item of an unticked parent) |
| Demo-ready | No (scripted offline run passes; Wi-Fi was not physically switched off, no backup video, no consented footage, frozen set not validated; tree has uncommitted reader work) |
| Last updated | 24 Oct 2026, 14:21 IST |

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
- ~~Hosted vision model chosen (cloud API); credits and rate limits checked~~ Dropped 24 Oct: the reader is local, no hosted model or key (see Decisions log)
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
- [ ] ~60 fake-app screenshots, 6 layouts, Hindi + English
- [x] ~300 synthetic portfolios (fake, mixed, real, no demat, partial coverage)
- [x] Synthetic payments ledger with scam pattern + mock Suspect Registry
- [ ] Frozen test set written by someone else, hashed
  - [x] Spec: `docs/FROZEN_SET_SPEC.md` (layout, minimum counts, author rules, HASH.txt recipe)
  - [x] Checker: `scripts/check_frozen.py` (structure, schemas, counts, coverage; writes HASH.txt once, then verifies); `data/frozen_example/` passes in `--example` mode
  - [ ] `data/frozen/` authored to the spec by someone who does not write the verdict rules
    - Received 24 Oct as `frozen-set.zip` (sha256 `371eb0a354f8e663694bfc3697d559495720a9eae4a71f503d4eb13e26b18a06`; two identical copies in Downloads); moved to `data/frozen/`, 79/79 files byte-identical to the zip; committed as received in 835441d (clips git-ignored by design, nothing edited). The author supplied no `HASH.txt`
    - `check_frozen.py`: counts above minimums (64 screenshots / 8 layouts, 127 rule cases, 76 brokers incl. 27 impersonations, 20 payees, 32 videos incl. 7 no-source and 7 off-centre crops) but FROZEN SET NOT OK: 32 problems, all "clip file not found in videos/". `videos/manifest.json` lists 32 clips; none exists in the folder, zip, Downloads, Desktop, Documents, Videos, data/media or D:\. `HASH.txt` not written
  - [x] Runner `scripts/run_frozen.py` (built, run on the example set only; the real set does not exist)
    - Refuses unless `check_frozen` passes incl. `HASH.txt` (tampered `payees.json` gives REFUSED, exit 2); never writes `data/frozen`; prints confusion matrix, FALSE CONTRADICTION count, reason-code accuracy, fallbacks, injection cases; writes `docs/VALIDATION.md` + `docs/validation_results.json`. Not run on the real set: the hash gate fails (no `HASH.txt`)

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
- [ ] Fake trading app screens + 60 screenshots, 6 layouts (A)
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
- [ ] Reader hardening (B; phases B and C of the validation goal skipped because the frozen-set check failed), uncommitted: `local.py` OCR clean-up (Devanagari digits, ₹ read as र), prompt rules, number validator, `tests/test_reader_numbers.py` (6 mocked tests), `scripts/make_dev_reader_set.py`, `scripts/eval_dev_reader.py`, `data/dev_reader/`. Before/after table not finished (the "before" run used images with a banner later removed)
- [ ] Backup demo video recorded
- [ ] Physical Wi-Fi-off rehearsal
- [ ] `npm --offline` install tested

## Test results

| Test | Target | Result |
|---|---|---|
| Claim fields read | ≥ 95% | gemma3:4b 56/56 on demo-001..003 (3 images, 0 invented claims); qwen2.5:3b 49/56 GPU, 53/56 CPU. Not yet the 60-screenshot set |
| Rule correctness (300) | 100% | 300/300 (1261 holding claims) |
| Source match top-1 (30) | ≥ 90% | 30/30 = 100% (dev clips, not the consented set) |
| Unindexed clips (sourceless) | NO_RECORD | 3/3 NO_RECORD; 0 misses returned MATCHES; slowest source search 1.23 s |
| Adversarial | 0 false MATCHES | Injection only so far: real-model tests in EN and HI, instruction text never becomes a claim and no verdict is MATCHES. Renamed broker, near-duplicate UPI and sourceless video suites still open |
| Comprehension | 5 / 5 | — |
| Result after consent | < 60 s | 0.78 s (demo-001, local) |
| Prompts per 1,000 customers | report | 133 (40 of 300 customers, one prompt per campaign); 40/40 prompted are injected scam-pattern customers, 0 others (synthetic ledger where the pattern was injected to fit the rule, so this is an upper bound) |
| First /api/video after fresh start | report | 3.09 s (models preloaded, GPU) |
| Source search < 5 s | < 5 s | GPU 2.17 s; CPU fallback (CUDA_VISIBLE_DEVICES=-1) 2.66 s |
| Full video result (read + video + check) < 60 s | < 60 s | GPU 11.50 s; CPU fallback 18.11 s |
| Offline demo run (`scripts/demo.py`) | all steps pass | 24 Oct 12:53: all 6 flows PASSED, "demo OK offline", 0 blocked attempts under the socket guard plus HF/transformers offline vars and a dead proxy (Wi-Fi not physically off). Earlier run (05:30) was reported as 7 steps |
| Full suite | green | `scripts/verify_all.sh --quick` (24 Oct 14:21 session): ALL CHECKS PASSED; pytest 112 passed (includes the uncommitted reader work), ruff clean (pytest, ruff, templates, frontend build/lint/test, example frozen set). Includes real-model injection tests EN and HI |
| Frozen-set checker on the real `data/frozen/` | pass | FROZEN SET NOT OK, 32 problems, all missing video clips; counts all above minimums (64 screenshots / 8 layouts, 127 rule cases, 76 brokers incl. 27 impersonations, 20 payees, 32 videos incl. 7 no-source and 7 off-centre crops). No `HASH.txt`; `run_frozen.py` not run on it |
| Frozen runner on `data/frozen_example/` (`--example`) | report | After the example set was fixed (24 Oct 13:13): outcomes 8/8, FALSE CONTRADICTION 0, reason codes 10/10, injection 1/1, reader fallbacks 0, screenshot fields 5/8. The 3 field misses are real reader errors, labels not changed: `ex_s1` the total copied into the single holding's `value_inr`; `ex_s2` Hindi "शेयर: 5000" read as `value_inr` 5000 instead of quantity. Earlier run on the broken example (12:53) was 6/8 outcomes, reason codes 8/10, fields 1/8, injection 0/1. Not a result on the real frozen set (does not exist) |
| Preflight (`scripts/preflight.py`) | GO | GO on all 10 checks at commit bf048c1 (shown last session, after the IPv6 port fix). Earlier first run, servers down, was NO-GO for `/health`, 7 stored checks and a dirty tree. Not re-run at 835441d (servers down). `tests/test_preflight.py`: a port held by a silent process is NO-GO |
| Offline kit make/restore (temp folder test) | manifest OK | 1361 files, 6.61 GB; make 47 s, manifest OK; restore 40 s into a temp clone and temp home, every file verified before copying. Not yet on the real pen drive |
| Demo wait times (from `docs/DEMO_DAY.md`) | report | 29-41 s in cache mode, 47-48 s in local mode |
| Peak memory, image (local reader, gemma3:4b) + video request at once | < 7.8 GB VRAM | 7181 MB peak on the whole GPU (includes 3740 MB already in use before start). Image 7.56 s, video 10.30 s concurrently |
| Local read, GPU hidden (backend `CUDA_VISIBLE_DEVICES=-1`, Ollama `num_gpu=0`) | < 60 s | demo-001 42.21 s, demo-002 44.65 s, demo-003 40.21 s per image, gemma3:4b, no fallback. Read alone is 40-45 s, so little margin on a CPU-only laptop in local mode |
| Local backend warm-up | report | ready after 48.1 s (CLIP, Whisper, EasyOCR, Ollama model) |
| Frozen-set checker on `data/frozen_example/` (`--example`) | pass | passes; combined hash `f1c77f42c8e4e3d5f3a6ac5334ab16b679ae987d83a433f418c9f8c0ab9ddaca` (re-hashed with `--rehash` after the example fixes; was `c5d57d97...5076`). This is the example, not the real frozen set, which does not exist yet |

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
| 23 Oct | RESOLVED (next rows): commit or git-ignore the SEBI CSVs | They total ~2 MB and hold public contact emails/phones; the project rules say not to commit large copies of public lists |
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
| 24 Oct | Money shows with ₹ ("₹3.98 crore", "₹1,07,000"), not "Rs" | project rules convention; the goal text said "Rs 3.98 crore" |
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

## Blockers

- Tesseract is not on PATH. Code must read the install path from config/env (`C:\Program Files\Tesseract-OCR`) or PATH must be set on each laptop.
- Environment note: Python on this laptop is 3.14.6, but the stack specifies 3.11. Node is 24.19 and npm is 11.17. Python Playwright 1.64 needed chromium-headless-shell build 1248, now installed.
- **The 32 frozen video clips are missing.** `data/frozen/videos/manifest.json` lists them, no file exists anywhere searched, so `check_frozen.py` fails and `HASH.txt` was not written; validation (`run_frozen.py`) and reader hardening against the set are blocked. To unblock: the set's author supplies the clips into `data/frozen/videos/` (then `check_frozen` writes `HASH.txt`), or the team decides to validate without videos, which needs a checker change logged as a decision.
- The Hindi UI strings (71 in the `ui` section, plus the new MOCK footer string) need a fluent reader, like the verdict templates.
- `data/registries/bse_equity.csv` cannot be fetched by script; a fresh clone needs it copied by hand (README lists it). Copy it onto the pen drive.
- The Wi-Fi-off rehearsal is not done: the offline proof so far is the socket guard (0 blocked attempts), not a physical disconnect.
- No backup demo video yet (last fallback in `docs/DEMO.md`).
- `npm --offline` install is untested; only the pip side of the offline kit is verified.
- Video: an off-centre 10% crop (top-left) matched only 35% of frames, so it gives NO_RECORD (a miss, never a false MATCHES). Consider multi-crop indexing or local features if the judges test this.
- The dev evidence key sits in `data/runtime/evidence.key` when `EVIDENCE_KEY` is unset. On this laptop `.env` now has an `EVIDENCE_KEY` (git-ignored); copy `.env` to the demo machine, otherwise the dev key file is used again.
- The reviewer UI is English only; its Hindi strings exist but are not toggled.
- The trigger rate comes from a synthetic ledger built to match the rule, so field precision is unknown.
- Video: all results are on dev clips. Re-run make/index/eval with the consented clips once the forms are signed.
- Frozen set has no `HASH.txt` (see the clips blocker). Until it is hashed and run, the rule-correctness claim rests on our own 300 synthetic portfolios, not a frozen set. The set's author supplied no `HASH.txt`; the clips also depend on consented footage.
- Local reader: Ollama and its models (`gemma3:4b`, `qwen2.5:3b`), EasyOCR weights must be on the demo machine; `make_kit.ps1` bundles them. Reader, validation runner, preflight, kit scripts and runbook are committed; the reader-hardening work (see Phase 5a) is not.
- Risk: with the GPU hidden, one local read takes 40-45 s (measured 40.21 to 44.65 s on demo-001..003), so the <60 s result target has little margin on a CPU-only laptop in local mode. The demo itself uses cache mode.
- Decision for the team: reader total guard hides the ad's internal inconsistency (₹99 crore total vs ₹3.98 crore of lines) from the customer; verdicts unchanged. See Decisions log.
- Local reader misreads on the example set (labels left as they are): the total copied into a single holding's `value_inr` (`ex_s1`), and Hindi "शेयर: 5000" read as `value_inr` 5000 instead of quantity (`ex_s2`). Screenshot fields are 5/8; the real-set number is unknown until `data/frozen/` exists. Hindi quantity misread is open for the local reader.
- Kit custody: the kit contains `.env` with `EVIDENCE_KEY`; the drive stays with the team.
- The Hindi "preparing" string (bank app, shown until warm-up finishes) needs the fluent Hindi reader.
- To confirm: `docs/DEMO.md` and `scripts/demo.py` still describe `LLM_PROVIDER=cache`, while the provider enum is now `local` / `offline`; check which path the demo run uses.

## Next up

1. Get the 32 clips into `data/frozen/videos/` from the set's author (owner to be named), then run `scripts/check_frozen.py` (writes `HASH.txt`) and `scripts/run_frozen.py` for the real numbers; or the team decides to validate without videos and logs the checker change as a decision — team / set's author
2. Finish and commit the reader hardening (rerun the "before" run on banner-free images, complete the before/after table), then run phases B and C once the set is hashed — B / Aryan
3. Physical Wi-Fi-off rehearsal following `docs/DEMO_DAY.md`, backup video, kit to the real pen drive, preflight rerun with servers up on the final clean commit — D / Aryan

## Changelog

- 24 Oct 14:21 — Frozen set received (`frozen-set.zip`, sha256 `371eb0a3...e18a06`, two identical copies in Downloads), moved to `data/frozen/` (79/79 files byte-identical to the zip) and committed as received in 835441d (clips git-ignored by design; nothing under `data/frozen` edited). Author supplied no `HASH.txt`. `check_frozen.py`: counts above minimums (64 screenshots / 8 layouts, 127 rule cases, 76 brokers incl. 27 impersonations, 20 payees, 32 videos incl. 7 no-source and 7 off-centre crops) but FROZEN SET NOT OK, 32 problems, all clip files missing from `videos/` (none found anywhere searched), so `HASH.txt` not written; phases B (reader hardening) and C (validation) skipped per the goal's rule. Reader hardening from the previous session still uncommitted (OCR clean-up, prompt rules, number validator, 6 mocked tests, dev reader scripts and set; before/after table unfinished). `verify_all.sh --quick`: ALL CHECKS PASSED, pytest 112 passed, ruff clean; servers down, preflight not run. Preflight GO ticked (GO on all 10 checks at bf048c1 after the IPv6 port fix; committed in bf048c1 and 3c6a6fa). New blocker: 32 frozen clips missing. Overall stays 67%.
- 24 Oct 11:17 to 13:13 (folded) — Frozen-set groundwork (spec, `check_frozen.py` write-once `HASH.txt`, `data/frozen_example/` re-hashed `f1c77f42...ddaca`, `run_frozen.py` with hash gate), free local claim reader (gemma3:4b 56/56 fields on demo-001..003, cloud providers removed, overall 64% to 67%), warm-up, offline-guard tests, memory and CPU-only measurements, preflight, kit make/restore (1361 files, 6.61 GB, manifest OK on a temp folder), `docs/DEMO_DAY.md`; committed in 2efc95a, fc6833d, 3c6a6fa.
- 23 Oct 22:45 to 24 Oct 05:30 (folded) — Docs, prerequisites and synthetic data; Goal 1 slice (screenshot to "0 of 3 found" in 0.78 s); broker one-typo rule; bank app and result screen; video source check on dev clips (30/30 top-1); encrypted evidence chain, reviewer console, trigger rate (133 per 1,000); reset script, offline demo run, fresh-clone test, `test_verdict_source.py`, `docs/DEMO.md`. Overall 48% to 64% (21 of 33) by 05:30.

