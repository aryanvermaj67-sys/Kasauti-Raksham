# Kasauti — Product Requirements (48-hour finale MVP)

Version 1.0 · 23 Oct 2026 · Team Alpha

## 1. Problem

Investment scams accounted for over 75% (about 76%) of the at least ₹22,495 crore lost to cyber fraud in India in 2025 (Ministry of Home Affairs data, reported by ThePrint, 21 Feb 2026; re-check the primary MHA source before the finale). The Round 1 deck uses an earlier snapshot, ₹19,813 crore and 77% (I4C data, reported by IANS, 3 Jan 2026). Both are sourced; use the later, larger figure in the finale deck and say "over 75%". The pattern: an AI-made endorsement video, then an "advisor" on WhatsApp or Telegram, then a fake trading app showing a growing portfolio, then repeated transfers to rotating personal accounts, then a "tax" demanded before any withdrawal. Victims keep paying because the ad and the dashboard look real.

Deepfake detectors give a probability, which falls sharply on new fakes and which a scammer can talk a victim out of. Meanwhile the records that would expose the scam already exist: the victim's own depository holdings, SEBI's broker list and @valid UPI handles, the RBI Alert List, and the official footage the deepfake was cut from.

## 2. Goal

Put the claim next to the record before the next payment. Show the customer two facts from their own record, not a score, and give them and the bank a ready evidence path.

### Success for the finale

The demo story runs end to end without help, offline:
a deepfake ad and a fake app showing ₹3.98 crore → one check → the customer sees ₹0 of those holdings in his record, the source speech the ad was cut from with the changed words marked, and a complaint ready to send.

## 3. Users

| User | Need |
|---|---|
| Retail bank customer mid-scam (primary) | Plain facts in Hindi or English that they can check themselves; a one-tap way to report or get help |
| Bank fraud reviewer | Evidence they can trust and act on; approve or reject escalation |

## 4. Scope

### In scope (MVP)
1. Holdings check from an app screenshot against mock Account Aggregator data
2. Broker check against the real cached SEBI intermediary list
3. Payee check: SEBI @valid UPI handle pattern + mock I4C Suspect Registry
4. Platform check against the real cached RBI Alert List
5. Endorsement check: fake video matched to its source in a mock official archive, transcript diff
6. Result screen in Hindi and English
7. Evidence pack with SHA-256 hash chain
8. Reviewer console: view evidence, approve/reject escalation
9. Validation test suite and timing report

### Out of scope
Live AA connection, real bank data, real public figures, lip-sync forensics, cross-bank warnings at scale, fully generated (sourceless) video detection beyond `NO_RECORD`, Tracks 01/02 extensions.

## 5. User flow

1. **Trigger.** Bank app shows "Check this investment" because (a) the customer tapped Check, or (b) a payment fits the scam rule (see FR-1).
2. **Share.** Customer uploads a screenshot and/or a video or link.
3. **Read.** Claim reader returns a claim list. Customer edits or confirms each claim.
4. **Consent.** Mock AA consent screen with OTP for a one-time holdings fetch.
5. **Test.** Router sends each claim to its connector; comparators and rules produce verdicts.
6. **Reveal.** Two-column result: "Your app says" / "Your record says", plus the video finding.
7. **Act.** Buttons: Report to 1930 (pre-filled), Call trusted contact, Bank callback, "I still want to pay".
8. **Review.** Reviewer sees the evidence pack, approves escalation; account goes to the (mock) Suspect Registry.

## 6. Functional requirements

### FR-1 Trigger
- FR-1.1 Manual "Check" button always available.
- FR-1.2 Rule trigger (prototype): new payee AND ≥3 transfers to new payees in 14 days with rising amounts, OR payee not a @valid handle while narration contains invest/IPO/trading keywords.
- FR-1.3 At most one prompt per campaign per customer. Triggers never use age, gender, language or region.
- FR-1.4 No payment is blocked.

### FR-2 Claim reader
- FR-2.1 Input: image (PNG/JPG) or video (MP4). Output: `ClaimSet` in the schema below, nothing else.
- FR-2.2 Provider set by `LLM_PROVIDER`; `cache` mode returns stored output keyed by the file's SHA-256.
- FR-2.3 Output is validated by Pydantic; invalid output is retried once, then the field is left empty for the customer to fill.
- FR-2.4 Instructions inside the artifact are ignored. The reader's output cannot set a verdict.
- FR-2.5 Customer must confirm the claim list before any record is checked.
- FR-2.6 Offline fallback if the hosted model is unreachable: Tesseract OCR with the Hindi language pack plus regex field patterns, producing the same `ClaimSet`. Optional local vision model (Ollama) only on a laptop with a GPU or 16 GB+ RAM.
- FR-2.7 Holding names are mapped to ISINs through `isin_master`; an unmapped name stays a claim with `isin=null` and is shown to the customer for correction.

### FR-3 Claim schema

```json
{
  "artifact_sha256": "hex",
  "language": "en|hi",
  "claims": [
    {"id": "c1", "type": "holding",
     "fields": {"instrument_name": "str", "isin": "str|null", "quantity": "int|null", "value_inr": "number|null"}},
    {"id": "c2", "type": "broker",
     "fields": {"name": "str", "sebi_reg_no": "str|null", "claims_registered": "bool"}},
    {"id": "c3", "type": "payee",
     "fields": {"upi_id": "str|null", "account_no_last4": "str|null", "ifsc": "str|null", "described_as": "broker|advisor|other"}},
    {"id": "c4", "type": "endorsement",
     "fields": {"person": "str", "quote": "str", "media_sha256": "hex"}},
    {"id": "c5", "type": "platform",
     "fields": {"name": "str", "category": "equity|forex|crypto|other", "claims_licensed": "bool"}}
  ],
  "portfolio_total_inr": "number|null"
}
```

### FR-4 Connectors (each returns `RecordResponse`)
| Connector | Source | MVP form |
|---|---|---|
| `aa_mock` | Depository holdings (CDSL and NSDL, both listed by Sahamati as FIPs) | Synthetic FI data in ReBIT equities + mutual-funds format v1.0.0; per-depository success/failure flag so partial-coverage cases can be tested. The fetch asks for Summary/Holdings only, never the Transactions section (deck: "transaction history, balances" are not collected) |
| `isin_master` | NSE and BSE equity lists (name to ISIN) | Cached CSV; used to map names read from a screenshot to ISINs before the holdings comparison |
| `sebi` | SEBI registered intermediaries (brokers, investment advisers, research analysts) | Cached CSV, normalized names + reg nos |
| `upi` | SEBI @valid handle format | Format rule only; SEBI Check is a lookup tool, not a downloadable dataset, so full verification is a mock |
| `suspect_registry` | I4C Suspect Registry | Mock list, read and write (the real registry is shared with banks, not public) |
| `rbi` | RBI Alert List (unauthorised forex) | Cached CSV, converted by hand if only published as PDF |
| `footage_index` | Official footage | Index of teammates' consented "official" clips |

All cached public files follow the rules in section 11 (Data sources).

### FR-5 Verdict rules (deterministic)

| Claim | MATCHES | CONTRADICTS | NO_RECORD |
|---|---|---|---|
| Holding | ISIN found, quantity within ±0 | Not found (or qty differs) AND all depositories in scope returned OK | Any depository failed or not in scope; no demat account |
| Broker | Exact normalized name or reg no on SEBI list | `claims_registered=true` and no exact or near match (similarity < 0.6) | Near match only (0.6–0.9): ambiguous |
| Payee | Valid @valid handle and not in Suspect Registry | In Suspect Registry, or described as broker but not a @valid handle | Bank account with no registry hit |
| Endorsement | Source found, transcript same | Source found (sim ≥ threshold), transcript differs: report changed time range | No source found |
| Platform | — (never MATCHES in MVP) | On RBI Alert List | Not on list |

Each verdict has `reason_code`, `evidence_ids[]`, and template params.

### FR-6 Video comparator
- FR-6.1 Sample 1 fps; perceptual hash + embedding per frame; nearest source clip by vote across frames.
- FR-6.2 Align by best frame offset; transcribe both with locally run Whisper (weights pre-downloaded, no network or account); word-level diff → changed time ranges.
- FR-6.3 Robust to re-encode (CRF 28–35), crop up to 10%, resize to 480p.
- FR-6.4 No lip-sync analysis in MVP. The Round 1 deck (Pitch 6) lists "changed words and lips"; change it to "changed words" or mark lips as future work.
- FR-6.5 Optional stretch, built last: a pretrained fake-video detector score shown only as a labelled "weak signal" and never used in a verdict; and a C2PA Content Credentials check where present (absence proves nothing). Both match Pitch 6 and Architecture 3.

### FR-7 Result screen
- FR-7.1 Two columns: "Your app says" / "Your record says", totals first, then per-claim rows.
- FR-7.2 Text only from templates (`messages_en.json`, `messages_hi.json`); language toggle.
- FR-7.5 Holdings sentences name the depositories actually queried ("CDSL", "NSDL" or "CDSL and NSDL") as a template parameter. The deck's Pitch 4 Hindi sentence names only CDSL; do not copy it as a fixed string. Seed wording from the deck: "Your app shows ₹3.98 crore of shares. None of them is in your name in the depository record."
- FR-7.3 Shows self-check steps: CDSL easi, monthly CAS, SEBI Check.
- FR-7.4 No score, no "verified" badge, nothing shareable outside the app.

### FR-8 Response actions
- FR-8.1 Pre-filled complaint text for 1930 / cybercrime.gov.in (copy + open link; no auto-submit).
- FR-8.2 Trusted contact call and bank callback are mocked buttons that log an event.
- FR-8.3 "I still want to pay" records the choice and allows the payment.
- FR-8.4 Outcome to response (Architecture 2):
  - MATCHES: shown as confirmed; no alert, no escalation.
  - NO_RECORD: "We could not verify this." plus steps to check alone (CDSL easi, monthly CAS, SEBI Check) and an optional bank callback; any detector score is labelled weak.
  - CONTRADICTS: complaint, trusted contact and callback offered; after reviewer approval the account is reported and other payers are warned.

### FR-9 Evidence
- FR-9.1 Every record response is stored with source, time, consent ID, SHA-256 and previous hash; the customer's shared files are hashed on receipt. Holdings are deleted after the check (Pitch 8), so for holdings the chain keeps the hash and a minimal result (ISINs claimed, found or not found), never the full holdings payload.
- FR-9.2 Evidence pack export: JSON + human-readable PDF/HTML listing hashes (for a BSA Section 63(4) certificate).
- FR-9.3 `verify_chain()` detects any tampering; tested.
- FR-9.4 Encrypted at rest; role-based access (customer, reviewer); every read logged; 30-day retention setting.

### FR-10 Reviewer console
- FR-10.1 Queue of checks with any CONTRADICTS.
- FR-10.2 Detail view: claims, records, verdicts, evidence hashes, chain status.
- FR-10.3 Approve → payee added to mock Suspect Registry + list of other customers who paid it. Reject → logged with reason.
- FR-10.4 One report alone never lists an account; reviewer approval required.

## 7. Non-functional requirements

| Area | Target |
|---|---|
| Claim reading | < 10 s per screenshot |
| Holdings fetch (mock) | < 30 s incl. simulated OTP |
| Source search | < 5 s on the demo index |
| Result after consent | < 60 s |
| Offline demo | Whole flow runs with no internet (`LLM_PROVIDER=cache`, cached lists) |
| Privacy | Holdings deleted after check; no contacts, gallery, SMS, location |
| Accessibility | Result screen understood by 5 of 5 non-technical adults |

## 8. Validation plan

| Test | Set | Target |
|---|---|---|
| Claim reading accuracy | 60 screenshots, 6 layouts, Hindi + English | ≥ 95% of fields before customer edits |
| Rule correctness | 300 synthetic portfolios (fake, mixed, real, no demat, partial depository coverage) | 100%; any miss is a bug |
| Source matching | 30 fakes after compression and cropping | ≥ 90% top-1; misses say "no source found" |
| Adversarial | Injected text in screenshot, renamed broker, near-duplicate UPI handle, mixed real+fake portfolio, sourceless video | Never a false MATCHES; never a CONTRADICTS without full coverage |
| Comprehension | 5 non-technical adults | 5 of 5 explain the result |
| Prompt rate | Synthetic transaction stream | Reported per 1,000 customers |

Rules for the tests:
- The frozen test set is written by someone who does not write the verdict rules, then SHA-256 hashed before the rules are tuned. Results are reported against that hash.
- Never hard-code a result. Every screen in the demo comes from the real pipeline, with `LLM_PROVIDER=cache` replaying only the claim reader's stored output.
- Run the demo once with Wi-Fi switched off before the finale.
- Report prompts per 1,000 customers from the synthetic ledger (scam pattern injected).

Note for the pitch: the 300-portfolio suite proves rule correctness, not detection accuracy in the wild.

## 9. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Scope too big for 48 h | Build the screenshot → verdict slice first; video second; cut anything not in the demo story |
| False CONTRADICTS on a real investor | Full-coverage rule (FR-5); partial → NO_RECORD; tested |
| Video matching fails on stage | Pre-tested demo clips; cached results; backup video |
| Live API / Wi-Fi failure | `cache` provider, local registry CSVs, recorded backup at hour 40 |
| Judges question figures | Re-verify every cited 2026 figure against its primary source before the finale |
| Victim told to ignore the check | Evidence is their own record shown by their own bank; acknowledged as a limit |

## 10. Open questions
- LLM provider for the live path: Amazon Nova on Bedrock vs Claude (decide hour 0; log in progress.md).
- Exact @valid UPI handle format: confirm against the SEBI circular.
- Rules to confirm with organisers: whether pre-written code is allowed or only data, designs and models; venue internet and power; whether paid cloud APIs are allowed; that the registered track is Track 03.
- Deck fixes for the finale presentation: Pitch 2 fraud figure (see section 1); Pitch 6 "and lips"; Pitch 7 and Architecture 3 "NSDL is to be confirmed" (Sahamati now lists both NSDL and CDSL, section 11; keep the full-coverage rule anyway); Pitch 4 Hindi sentence names only CDSL; Pitch 10 says broker and payee checks run "on real public lists", but the @valid lookup and Suspect Registry are mocks.
- Facts to verify or drop before judges ask: the Supreme Court hash-value ruling (May 2026), Singapore "2,700+ scams disrupted", FBI "77% didn't know", the face-swap source-attribution paper, CBI ABHAY.

## 11. Data sources

Public and free to access, but several arrive as search pages or PDFs, so budget extraction time. Record the source page, download date and SHA-256 of every file in `data/SOURCES.md`. Public does not mean free to republish: cite them, and do not commit large copies to a public repo without checking each site's terms.

| Source | Use | Form | Notes |
|---|---|---|---|
| SEBI registered intermediaries (sebi.gov.in) | `sebi` connector | Lists by category, searchable on the site | May need page-by-page export |
| RBI Alert List (rbi.org.in) | `rbi` connector | Often a PDF | Convert to CSV; note the version |
| NSE and BSE equity lists | `isin_master` | Downloadable files of listed securities | NSE can block scripted downloads: download in a browser |
| ReBIT AA schemas, equities and mutual funds (specifications.rebit.org.in) | Format of `aa_mock` | Public schema + docs | Equities: Account has Profile (Holders), Summary (Investment, Holdings) and Transactions; each Holding has `isin`, `isinDescription`, `issuerName`, `units`, `lastTradedPrice`; version 1.0.0 |
| Sahamati FI-type page, non-banking FIPs (sahamati.org.in) | Cite for "CDSL and NSDL provide data over AA" | Public web page | Lists both depositories with equity shares, mutual fund units, ETF, IDR, CIS, AIF, InvIT, REIT activated; last updated 29 May 2026 when checked on 23 Oct 2026 |
| Sahamati FIP-AA mapping (sahamati.org.in/fip-aa-mapping) | Context only | Table refreshed daily | Rows did not load in a text fetch; open in a browser to read |

Cannot be downloaded, so mocked and labelled as mocks everywhere: real Account Aggregator data (only a regulated Financial Information User can fetch it), the I4C Suspect Registry, a bulk list of SEBI @valid handles, bank payment records, and real official footage. No real person's data or likeness is used.

## 12. Deployment pathway (from the Round 1 deck, Pitch 9; for the pitch, not built)

Operating owner: the bank's Fraud Risk Management team. Product owner: digital banking.

| Phase | Scope |
|---|---|
| 1 Pilot | One bank, opt-in "Check an investment" button; holdings and registry checks only |
| 2 Prompts | Payment-pattern prompts for consenting customers; reviewer console; measure prompt rate and outcomes |
| 3 Video source checks | Index of official public footage, run once for all banks because it holds only public data |
| 4 Scale | More banks and payment apps; later extensions (loan-app morph check, cloned-voice family check) are outside this build |

Plugs into: the mobile banking app (one screen module), the fraud rules engine (a new trigger), the bank's existing Account Aggregator FIU integration (reused consent flow), the 1930 / cybercrime.gov.in complaint flow, and the I4C Suspect Registry feed. No payment is held by default. A check takes about a minute, mostly the customer's own OTP and confirmation.
