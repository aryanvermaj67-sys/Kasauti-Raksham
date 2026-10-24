# Kasauti test kit: how to reproduce every result

The organisers' rubric says the test workflow is part of the submission, completeness matters as much as accuracy, and any open dataset may be used with reproducibility instructions. This page is that workflow. Every number below comes from a command in this repository; nothing is typed in by hand.

## What data the tests use (and what is open)

| Test data | Where it comes from | Open? |
|---|---|---|
| SEBI registered brokers, advisers, research analysts; RBI Alert List; NSE and BSE equity lists | Public lists, downloaded with `scripts/fetch_registries.py` and `scripts/fetch_sebi.py`; every file has a row in `data/SOURCES.md` (page, date, SHA-256) | Yes, public |
| 300 synthetic portfolios (fake, mixed, real, no demat, partial coverage) | `scripts/gen_portfolios.py --n 300 --seed 42`, in the ReBIT Account Aggregator format, built from the public lists above | Generated from public data, seeded |
| 60 fake-app screenshots, 6 layouts, Hindi and English | `scripts/make_fake_app_screens.py --seed 7` | Generated, seeded |
| 64 screenshots, 130 rule cases, 76 brokers, 20 payees, 9 adversarial images | `data/frozen/`, written by a person who does not write the rules, hashed in `data/frozen/HASH.txt` | In the repo |
| Video source matching | Teammates' consented clips (`scripts/make_test_clips.py`), plus 6 development clips from `scripts/make_dev_clips.py` | Consented, not public |

There is no open dataset of fake trading-app screenshots or of AI-made endorsement videos of Indian officials, so the screenshot and rule tests use synthetic data built from the open lists. We say that plainly rather than call a synthetic set "real-world". If time allows, a public speech or deepfake-video dataset can be added to the video test with the same script.

## Reproduce from a fresh clone

Python 3.11 to 3.14, Node 20+, ffmpeg on the PATH. Models are not in the repo: see `docs/SETUP_LOCAL_MODELS.md` (Ollama with `gemma3:4b` and `qwen2.5:3b`, EasyOCR weights, Tesseract with the Hindi pack).

```bash
pip install -r backend/requirements.txt -r backend/requirements-local.txt
cd frontend && npm install && cd ..
python scripts/fetch_registries.py        # public lists (needs internet once)
python scripts/gen_portfolios.py --n 300 --seed 42
```

Then run the checks. Each one prints its result and exits non-zero on a miss.

| # | Command | What it proves | Result on 25 Oct 2026 |
|---|---|---|---|
| 1 | `sh scripts/verify_all.sh --quick` | backend tests, lint, templates (English and Hindi), frontend build, lint and tests, example set check | all pass; 156 backend tests |
| 2 | `python scripts/run_portfolios.py` | verdict rules on the 300 synthetic portfolios, 1,261 holding claims | 300 of 300 correct |
| 3 | `python -X utf8 scripts/run_frozen.py` | the frozen set end to end (refuses to run unless `HASH.txt` matches): rules, brokers, payees, injected-text images, claim reader on 64 screenshots | 274 of 274 verdicts, 0 false contradictions, 307 of 307 reason codes, 607 of 632 screenshot fields (96%), injection 5 of 5 |
| 4 | `python -X utf8 scripts/make_fake_app_screens.py --score` | claim reader on the 60 generated screenshots | 571 of 584 fields (97.8%) |
| 5 | `python scripts/video_eval.py` | source matching on the development clips, network disabled | 30 of 30 top-1, 3 of 3 unindexed clips give "no record" |
| 6 | `python scripts/video_eval.py data/media/clips/labels.csv --out docs/VIDEO_EVAL` | the team's consented clips: changed words found, unchanged clips not flagged, no-source clips give "no record" | **pending the recordings** |

`LLM_PROVIDER=local` (the default) uses EasyOCR and Ollama on this machine; no network call leaves the laptop (`scripts/offline_guard` fails any that tries). The run-by-run history is in `docs/VALIDATION_SUMMARY.md`; raw per-item results are in `docs/validation_results_run*.json`.

## Error rates, including false positives

A false positive here is a "contradicts" verdict on something that should not contradict.

| Measure | Result | Where |
|---|---|---|
| False contradictions on items that should match or have no record | **0 of 165** (78 should match, 87 should be "no record") | run 3 above |
| Genuine investors (portfolios in the `real` category) shown "matches" | all of them, 300 of 300 portfolios correct | run 2 |
| Wrong outcome of any kind | 0 of 274 | run 3 |
| Screenshot fields misread | 25 of 632 (4%) on the frozen set; 13 of 584 (2.2%) on the generated set | runs 3 and 4 |
| Reader fell back to the offline reader | 0 of 64 | run 3 |

The frozen set was used to find and fix bugs between runs (run 1: 251 of 274 outcomes, 14 false contradictions), so it is not a blind test. `docs/VALIDATION_SUMMARY.md` lists every post-freeze change and why. The 60 generated screenshots were also used for tuning. A blind check needs images the team has never seen: the judges' own screenshots in the live demo are exactly that.

## Failure cases we know about

1. **Misread screenshots (25 fields).** Scrambled table columns, a zero printed inside a firm name read as the letter O (`Angel 0ne`), a digit 9 read as 1 in Hindi amounts, an ISIN that loses a character, two platform names. The customer corrects every claim on the confirm screen before the check runs.
2. **A page where the model drops a holding.** The retry catches it when the lines do not add up to the printed total; if there is no printed total it does not.
3. **Video:** an off-centre 10% crop matches only about a third of frames, so it gives "no record" (a miss, never a false "matches"). A fully generated video has no source, so it gives "no record", never "real". Source matching on real consented clips has not been run yet.
4. **No lip-sync or voice-clone analysis.** Only changed words against a found source.
5. **Crypto and forex claims** have no holdings record: only the RBI Alert List and the payee checks run.
6. **A customer with an account at a depository we could not reach** is never told "not in your name": partial coverage gives "no record".
7. **CPU only:** a read takes 20 to 80 seconds instead of 2 to 7 on the GPU.

## Completeness: what is tested and what is not

| Area | Tested | Not tested |
|---|---|---|
| Verdict rules (holdings, broker, payee, platform, endorsement) | one match, one contradiction, one no-record and one adversarial case each; 300 portfolios; 130 frozen rule cases | live Account Aggregator (mocked, labelled as mock) |
| Claim reader | 64 + 60 screenshots, English and Hindi, 6 layouts, 5 injected-instruction cases; the model cannot change a verdict | handwriting, photos of a screen at an angle |
| Text in images is data | injected English and Hindi instructions; verdicts unchanged | |
| Evidence chain | hash chain verifies; tampering is detected | |
| Offline operation | network guard on the demo run | a physical Wi-Fi-off run on the demo laptops |
| Video source check | development clips | the consented clips (pending) |
| Hindi messages | placeholders and keys match English | UI strings not yet reviewed by a Hindi reader |
