# Kasauti — 3-minute demo script

Every line of on-screen text below was copied from the running app (`scripts/demo.py`, 24 Oct 2026, `LLM_PROVIDER=cache`, network guarded). Dev clips are used for the video until the consented clips are recorded.

## Before going on stage

1. `scripts/reset_demo.ps1` (or `.sh`): prints before/after counts and ends `reset OK`. Registry back to its 79 MOCK seed entries, reviewer queue 0.
2. `scripts/demo.ps1` once as a rehearsal: must end `demo OK offline`. It resets again at the start.
3. Start the two servers for the live demo (see README "Run the demo") and switch Wi-Fi off. Open `http://localhost:5173/app?customer=SYN-C0001` (phone width) and `http://localhost:5173/reviewer` in a second tab.
4. Have ready: `data/demo_cache/demo-001.png` and `data/media/fakes/dev_01_fake.mp4`.

## Script

| Time | Click | Expected on screen |
|---|---|---|
| 0:00 | (talk) The fake app shows a ₹3.98 crore portfolio and asks for another deposit; the ad uses a "public figure" (a teammate, with consent). | Bank app header with "MOCK bank login, synthetic customer" and the MOCK footer |
| 0:20 | **Check an investment**; choose `demo-001.png` as the screenshot and `dev_01_fake.mp4` as the video; **Read the claims** | "Check what we read. Correct anything that is wrong." with the holdings, broker, payee and the video quote |
| 0:40 | Type `DEV clip speaker` in the endorsement's person field; **Continue** | "Allow a one-time holdings check", "MOCK Account Aggregator consent. No real data is fetched.", "OTP sent to your phone (MOCK OTP: 123456)" |
| 0:55 | Enter `123456`; **Approve and check** | "What we found" · "Your app shows ₹3.98 crore of shares in 3 holdings." · "None of them is in your name in the CDSL and NSDL record." |
| 1:05 | Scroll the result | Reliance Industries 5,000, Tata Consultancy Services 3,000, Infosys 8,000: each "Not in your name at CDSL and NSDL." / "Does not match your record" |
| 1:20 | | "Zyphra Stock Club is not on the SEBI list of registered intermediaries." · "Registered brokers collect money through @valid handles. zyphrastock.invest@mockupi is not one." |
| 1:35 | | DEV clip speaker: "move all your savings into one tip." — "The original video exists, but the words were changed at 0:11-0:13. Original words: "build an emergency fund first."." |
| 1:50 | Toggle language (top button) | Same result in Hindi; Noto Sans Devanagari renders offline |
| 2:00 | **Report to 1930** area | Pre-filled text starting "I want to report a possible investment fraud. An app or broker called Zyphra Stock Club showed me ₹3.98 crore of shares. My depository record (CDSL and NSDL) shows 0 of these 3 holdings in my name. The app asked me to pay zyphrastock.invest@mockupi." It names the video clip, the changed range and the pack id. "Nothing is sent automatically." |
| 2:15 | Reviewer tab: open the newest check in the queue | "Hash chain intact (chain intact: 9 entries checked)" |
| 2:25 | Type a reason; **Approve** | "Added to the Suspect Registry (MOCK): zyphrastock.invest@mockupi Other customers who paid it: SYN-C0011 and SYN-C0108 and SYN-C0123 and SYN-C0202 and SYN-C0217" |
| 2:35 | Export the evidence pack | "Evidence pack pack-chk-… written"; the HTML says "Hash listing to support a certificate" (not a legal certificate) and "Chain verification: PASSED" |
| 2:45 | Bank app as `?customer=SYN-C0011` | "Before you pay again" · "You paid zyphrastock.invest@mockupi. A bank reviewer has since reported it to the Suspect Registry (MOCK)." · "Your payment is not blocked. You can check the investment first." |

Optional if asked: `demo-002.png` (customer SYN-C0028) shows a MATCHES screen ("All 4 are in your name in the CDSL and NSDL record.", no 1930 button); `demo-003.png` (SYN-C0025) shows NO_RECORD ("We could not check every depository (NSDL did not respond), so we cannot say whether these shares are yours.").

## If something fails

1. **Cached output** (default): `LLM_PROVIDER=cache` replays the claim reader's stored output for the demo screenshots. Only the reader is cached; rules, records and the evidence chain run live.
2. **Offline reader**: restart the backend with `LLM_PROVIDER=offline` (Tesseract with the Hindi pack + regex; Tesseract must be at `C:\Program Files\Tesseract-OCR` or `TESSERACT_CMD`). Use for a screenshot that is not in the cache.
3. **Recorded backup video** of this script. Not recorded yet (Phase 4 item); record it from a `demo OK offline` run.

If the video step hangs, check the backend log for "video models ready"; on a laptop without a GPU it reads "(cpu)" and the clip still finishes (measured 18.11 s full result on CPU, see below).

## Measured on this laptop (24 Oct 2026, dev clip `dev_01_fake.mp4`, API timing in `scripts/demo.py`)

| | GPU (cuda) | CPU (`CUDA_VISIBLE_DEVICES=-1`) | Target (PRD §7) |
|---|---|---|---|
| Source search | 2.17 s | 2.66 s | < 5 s |
| Full result (read + video + check) | 11.50 s | 18.11 s | < 60 s |

## Q&A sheet

**"Isn't this just a lookup?"** The lookup is the point: a scammer can fake the screen, the ad and the voice, but not the customer's depository record, SEBI's list or the original footage. The work is in getting a fair answer from it: reading an ad or app screenshot into a fixed claim schema, mapping share names to ISINs (358 ambiguous names map to no ISIN; the customer picks), never saying "contradicts" without every depository answering, a broker rule that tells an invented name from a one-letter typo of a real firm, finding the source clip and the changed words with time ranges, and a hash-chained evidence pack a reviewer can act on.

**"What about a fully AI-generated video?"** There is no source to find, so the video gives "No record found", never "real". On the dev set, 3 of 3 unindexed clips gave NO_RECORD and none gave MATCHES. The screenshot's holdings, broker and payee are still checked, and those are what the money depends on. A detector score was not built (PRD stretch item); if added it may appear only labelled "weak signal".

**"Why would a victim share a screenshot?"** They want to know if their "profit" is real before paying again. The bank can also prompt them when a payment fits the scam pattern (FR-1.2); the prompt asks for a check and never blocks the payment. It stays voluntary: some victims will never run a check (README, Known limits).

**"False positives?"** Holdings are CONTRADICTS only if every depository in the consent scope answered; partial coverage gives NO_RECORD (demo-003). A broker name within one typo of a registered firm gives NO_RECORD and names the firm. Ambiguous share names map to no ISIN. Rule correctness is 300/300 on synthetic portfolios, which proves the rules, not reading accuracy in the wild. A single report never lists a payee: a reviewer must approve.

**"Consent and privacy?"** One-time AA consent with OTP (MOCK in the prototype). The AA mock returns only the holdings summary, never PAN, mobile or transactions. The evidence chain keeps hashes and which claimed ISINs were found, not the holdings; it is Fernet-encrypted, every read is logged with the reader's role, and evidence is purged after 30 days. No contacts, gallery, SMS or location (PRD §7).

**"Who is the reviewer, and where is the login?"** A bank fraud reviewer. The prototype has no login: the role comes from a MOCK `X-Role` header. The backend still refuses evidence to any role but reviewer (403). A real bank would use its staff SSO; this is a prototype limit.

**"133 prompts per 1,000 customers: is that realistic?"** It is an upper bound on a synthetic ledger where the scam pattern was injected to fit the rule (40 of 300 customers, all 40 injected, one prompt per campaign). Field precision is unknown until it runs on real transactions.

**"Is the video match tested on real footage?"** All video numbers (30/30 top-1, 3/3 unindexed NO_RECORD) are on 6 dev clips made by `scripts/make_dev_clips.py`, not the consented set. The consented clips are recorded after the forms are signed, then `scripts/video_eval.py` is re-run. Known miss: an off-centre 10% crop gives NO_RECORD (a miss, never a false MATCHES).
