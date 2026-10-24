# Judging plan: schedule, rubric, what we show

From the organisers' "Round 2 Judging Rubric" (`Final Rubric.pdf`) and their instructions of 25 Oct 2026.

## Schedule

| When | What | We need |
|---|---|---|
| **11:00** | Code freeze and submission deadline | Last commit pushed, tag `v1.0-demo`, test kit results saved, nothing running half-way. Stop building at 10:30 |
| **11:00 to 14:00** | Preliminary judging (30 to 10): jury of 2, about **12 minutes per team**, no slides | A live demo on inputs the **judge picks**, then a conversation. A technical team checks code completeness and runs plagiarism checks at the same time |
| **15:00 to 16:30** | Final presentation, top 10, full jury of 6: **6 minutes presentation + 3 minutes Q&A**, quick demo inside the presentation | The Round 1 deck, corrected (`docs/DECK_FIXES.md`), cut to 6 minutes with the demo as the middle 2 minutes |

## Use `LLM_PROVIDER=local` for judging, not `cache`

The rubric asks for a prototype that "runs end to end, live, on inputs the judge picks". `cache` replays stored reader output for our three demo screenshots only, so it fails on a judge's own image and would score 1 ("nothing runs on new input"). Start the backend with the default `LLM_PROVIDER=local` (EasyOCR + Gemma on the laptop). A fresh read takes about 2 to 7 seconds on the GPU (up to 80 on CPU); keep `cache` only as the fallback in `docs/DEMO_DAY.md`. Warm the model before the jury arrives.

## Stage 1 (30 to 10): rubric and our answer

| Criterion (weight) | What scores 5 | What we show | Honest gap |
|---|---|---|---|
| Working prototype (25) | Runs live on inputs the judge picks | Judge hands us a screenshot (or we make one on the spot with `scripts/make_fake_app_screens.py`); read, confirm, consent, result, 1930 text, reviewer approval, evidence pack | A judge's video is checked only against our own consented clips; any other clip correctly gives "no record found". Say so first |
| Spot-check results and measured accuracy (30) | Most kit samples right; error rates including false positives on unseen data; names failure cases | `docs/TEST_KIT.md`: 274 of 274 verdicts, 0 false contradictions of 165, 96% of screenshot fields, named failure list. Offer to run the judge's own image as the unseen test | The frozen set was used for fixing bugs, so it is not blind; the judge's image is |
| Own engineering contribution (15) | Substantial own code; any member can explain it | Rules, router, evidence chain, the claim-repair logic (`reader/local.py`), the video comparator. Each member explains one part: see the table below | Everyone must be able to walk through their part; practise once |
| Alert and response flow (15) | A person sees a clear alert and can act; safeguards running | Result screen in Hindi and English, report to 1930 pre-filled, call my son, bank callback; reviewer console with human approval before anything is shared; evidence pack | Account Aggregator, Suspect Registry, @valid lookup and the payments ledger are labelled mocks |
| Delivery against Round 1 plan (15) | Built the plan, or cut scope on purpose and says why | Table below | |

### Round 1 plan against what is built

| Round 1 promised | State |
|---|---|
| Holdings check from a screenshot (mock AA) | Built, live |
| Broker and payee checks | Built: broker on the real SEBI list; payee on mock @valid and Suspect Registry (the deck must say so) |
| Source check of a changed endorsement video | Built; tested on development clips; consented clips being recorded |
| Hindi and English result screen | Built; Hindi reason-code messages reviewed by a Hindi reader on 25 Oct; UI strings not yet |
| Evidence pack with hashes | Built; chain tamper test passes |
| Reviewer console | Built |
| 60 screenshots, 300 portfolios, 30-video test, 5-adult comprehension test | 60 screenshots and 300 portfolios done; 30-video test and comprehension test pending |
| Cut on purpose | Lip analysis (words only), live Account Aggregator, real public figures |

## Stage 2 (final): rubric and our answer

| Criterion (weight) | What scores 5 | Prepare |
|---|---|---|
| Live user journey (25) | Works live on a scenario the jury can vary; the whole path from attack to alert, action, review | The 2-minute demo inside the 6 minutes: ad, screenshot, check, result, 1930, reviewer approval, a second customer warned. Let a juror change the broker name or the UPI handle |
| Adversarial robustness (20) | The team shows how an attacker would evade it, what it misses, what they would change | Prepare answers from `docs/TEST_KIT.md` failure cases: a fresh mule account (not in any registry gives "no record"), a cropped or re-edited video (off-centre crop is missed), a fully generated video (no source), a firm with a look-alike name (near-match is flagged, not trusted), text in the image telling the AI what to say (ignored by design). Never claim it cannot be fooled |
| Problem and user understanding (20) | A specific user and threat grounded in Indian UPI and banking fraud | Pitch 2 with the corrected ₹22,495 crore figure and the Pune case |
| Deployability and scale (15) | Path into a bank or UPI app; who runs it; cost; what a pilot needs | Pitch 9. Have a one-line cost answer ready: it runs on the bank's own servers with free local models, no per-check fee to a vendor; give a number only if the team has one |
| Communication and Q&A (10) | Clear, on time, direct answers including "we don't know" | Practise to 6 minutes; agree who answers what |
| Responsible AI and handling mistakes (10) | Shows what a genuine user flagged by mistake goes through, and how fast; alert says why; privacy safeguards running | Demo `demo-002` (a genuine holder sees "All 4 are in your name", no report button) and `demo-003` (a depository did not answer: "we could not verify", never "not in your name"). Show the reviewer console and that holdings are deleted after the check |

## Who explains what, and who speaks which clip

Official clips for the video test, from `Kasauti_Altered_Scripts.pdf`:

| Member | Clips | Part to be able to explain (suggested, confirm in the team) |
|---|---|---|
| Aryan | S01 (English), S06 (Hindi) | Claim reader and rules, evidence chain |
| Himanil | S02 (Hindi), S05 (English, demo clip) | Video source finder |
| Mudit | S03 (English), S08 (Hindi) | Data, fake apps, test kit |
| Rajat | S04 (Hindi), S07 (English) | Bank app, reviewer console, pitch |

The clip owners are fixed. The "part to explain" column is a proposal; the A–D role names are still to be confirmed by the team.
