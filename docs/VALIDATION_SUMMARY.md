# Frozen-set validation: what changed and what is left

Scope: **no-video** (the 32 video clips are not run). Set: `data/frozen`, combined hash `d2bfe2f3…40ec`, written by someone who does not write the verdict rules. Reader: `LLM_PROVIDER=local` (EasyOCR + gemma3:4b, Tesseract second reading for identifiers), on the GPU. The frozen set was used to find and fix bugs, so these are not blind numbers: every rule or reader change after the first run is a post-freeze change, listed below with its tests. No frozen id, name or figure appears in app code or tests (checked).

## Runs

| Run | Verdict outcomes right (of 274) | FALSE CONTRADICTION | reason_code right (of 307) | Screenshot fields right (of 632) | Reader fallbacks | Injection |
|---|---|---|---|---|---|---|
| 1 (`VALIDATION_RUN1.md`, before any fix) | 251 | 14 | 280 | 372 | 4 | 5/5 |
| 2 (rules fixed, model warmed first) | 270 | 0 | 306 | 354 | 8 | 5/5 |
| 3 (new model layout) | 269 | 1 | 304 | 450 | 0 | 4/5 |
| 4 (second OCR, grounding, ISIN repair) | 269 | 0 | 305 | 535 (counting ISINs the app fills in from the name separately) | 0 | 4/5 |
| 5 (payee fallback, completeness retry, units) | 270 | 0 | 306 | 582 | 0 | 5/5 |
| 6 (final: value fill, page order) | 270 | 0 | 306 | 593 | 0 | 5/5 |

Final confusion matrix (run 6): MATCHES 78/78 correct; CONTRADICTS 106 correct, 3 given NO_RECORD; NO_RECORD 86 correct, 1 NOT_READ. Seconds per screenshot (read, GPU): 2.1 to 14.6, mean about 5. On the CPU (`CUDA_VISIBLE_DEVICES=-1`, subset of 3): 21 to 83 s per screenshot (OCR 9 to 41 s, model 12 to 42 s). Prompt rate on the synthetic ledger: 133 per 1,000 customers (an upper bound; the pattern was injected to fit the rule).

## Failures left (4 verdicts) and their cause

| Items | Expected / got | Cause |
|---|---|---|
| rc-024, rc-025, rc-127 | CONTRADICTS / NO_RECORD (both `HOLDING_NO_DEMAT`) | **Label vs PRD.** PRD FR-5 says "no demat account" is NO_RECORD; the frozen labels say a customer with no account anywhere contradicts a holding claim. Both are defensible: product decision, not a bug. Nothing changed. |
| a009 | NO_RECORD / NOT_READ | **Label vs design.** The screenshot reader never produces endorsement claims (those come from video), so a frame from a promo video yields no claim. |

## Screenshot fields still wrong (39 of 632)

OCR limits and look-alike glyphs, not rules: a table whose columns EasyOCR scrambles (s037), a digit zero printed in a firm name read as the letter O (`Angel 0ne`, `Zer0dha` is repaired only inside a lower-case word), a digit 1 for a letter l in a handle (`va1idmock`), an ISIN with a dropped character, UPI ids the label gives with a space (`profit king@mockupi`), two platform names the model got wrong, and a few values on pages with an unusual amount layout. The customer sees every claim on the confirm screen and corrects it before the check.

## Post-freeze changes (each with tests in `backend/tests/test_post_freeze_rules.py` unless noted)

| Change | Why (what the first run showed) |
|---|---|
| A typo anywhere in a broker name, generic words included, is a near match | 10 false contradictions: a one-letter typo in "Securities" or "Broking" fell outside the distinctive-words test |
| Devanagari names are normalised as letters, not erased | A Hindi name normalised to an empty string and matched any one-letter key (a false near match) |
| A registration number held by nobody falls back to the name logic | "reg no mismatch" was reported for a number on no entry |
| A bare name that longer listed names begin with is ambiguous | A company that split in two: the bare name mapped to one ISIN and the customer holding the other was contradicted |
| An ISIN on neither list is NO_RECORD (unmapped), ahead of partial coverage | An OCR misread of an ISIN would have been reported as "not in your name" |
| OCR identifier repairs (`\|NZ` reg no, `@` read as a letter in handles, a capital O inside a word) | Registration numbers and handles were lost, and `ZerOdha` matched the real broker |
| ISIN check-digit repair (look-alike swaps, only to a listed ISIN) | 71 ISIN misreads (O for 0) |
| Ollama keep-alive, 1,500-token cap, model asked for a holdings list plus one broker, payee, platform | 8 reads timed out: gemma looped on empty claims, and the model unloads after 5 idle minutes (cold start 100 s+) |
| Tesseract second reading for UPI handles and registration numbers | EasyOCR drops "@" in about a third of the screenshots |
| Words for null, page headings and unsupported "registered" claims are removed; an ISIN copied onto two holdings stays on one | The model invented brokers from headings and a "registered" claim the text did not make |
| Holdings that do not add up to the printed total get one retry; values filled from printed rupee amounts; L and Cr units; page order | The model dropped lines (or put a name in the UPI field) and left "₹ 4.26 L" null |

Harness changes (`scripts/run_frozen.py`): the model is warmed up first, as the backend does at startup; ISINs the app fills in from the name are counted as such, not as misreads; security names are compared the way the app maps them (case, punctuation, Ltd ignored).
