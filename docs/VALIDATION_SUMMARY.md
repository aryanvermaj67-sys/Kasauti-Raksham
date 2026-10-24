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
| 6 (value fill, page order) | 270 | 0 | 306 | 593 | 0 | 5/5 |
| 7 (final: no-demat contradicts, sourceless frame via the video route, value re-fill, ISIN from page, payee wording grounded) | **274** | 0 | **307** | **603** | 0 | 5/5 |

Final confusion matrix (run 7): MATCHES 78/78, CONTRADICTS 109/109, NO_RECORD 87/87. Seconds per screenshot (read, GPU): 1.9 to 7.0. On the CPU (`CUDA_VISIBLE_DEVICES=-1`, subset of 3): 21 to 83 s per screenshot (OCR 9 to 41 s, model 12 to 42 s); a CPU-only laptop now gets 3x the model time limit (`KASAUTI_READ_TIMEOUT` overrides), so it no longer falls back to the offline reader. Prompt rate on the synthetic ledger: 133 per 1,000 customers (an upper bound; the pattern was injected to fit the rule).

## Failures left: none in verdicts

The three cases that failed in run 6 were decisions, now taken:

| Items | Decision |
|---|---|
| rc-024, rc-025, rc-127 | A customer with no demat account at any depository, where every depository answered, is **CONTRADICTS** (`HOLDING_NO_DEMAT`), not NO_RECORD. It follows the rule "CONTRADICTS only if every depository was queried successfully" and the frozen labels. If a depository fails, it is still NO_RECORD (partial coverage). PRD FR-5, both templates, `test_rules.py`, `gen_portfolios.py` and the 60 no-demat synthetic portfolios were changed to match. |
| a009 | A frame from a promo video is a video item, not a screenshot. The harness now makes the frame a 3 s silent clip and runs the real source search (`POST /api/video`), then the rules: NO_RECORD `ENDORSEMENT_NO_SOURCE`. This runs against the dev footage index; with the real official clips indexed it must be rerun. |

## Screenshot fields still wrong (29 of 632)

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
| Values the model scaled wrongly ("₹ 7.10 L" as 71 lakh) are read again off the page after the number check; an ISIN the model garbled is replaced by the listed, check-digit-valid ISIN the page prints (never when the page prints that exact ISIN); a payee is "broker" or "advisor" only if the text uses the word | Run 6 left 14 values null and one ISIN dropped a digit; a payee called "broker" with no such word would have produced a contradiction |
| A holding claim where every depository answered and none holds an account is CONTRADICTS | see above |

Harness changes (`scripts/run_frozen.py`): the model is warmed up first, as the backend does at startup; ISINs the app fills in from the name are counted as such, not as misreads; security names are compared the way the app maps them (case, punctuation, Ltd ignored).
