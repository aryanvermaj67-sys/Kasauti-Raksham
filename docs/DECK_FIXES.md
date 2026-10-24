# Deck fixes for the finale (from `Kasauti_Round1_Alpha.pdf`)

The Round 1 PDF is a finished file (no editable source on this laptop), so these are exact replacements to make in whatever tool the finale deck is built in. Each claim was checked on 25 Oct 2026; sources at the end. Nothing here changes what Kasauti does.

## Replace

| Where | Now says | Change to |
|---|---|---|
| Pitch 2, stat box and source [1] | "77% of the 19,813 crore lost to cyber fraud in India in 2025 went to fake investment schemes [1]" | "Over 75% of the ₹22,495 crore lost to cyber fraud in India in 2025 went to investment fraud [1]". Source [1]: ThePrint, 21 Feb 2026 (Ministry of Home Affairs data) |
| Pitch 3, "His holdings" | "CDSL shares it via Account Aggregator with consent [7]" | "CDSL and NSDL share it via Account Aggregator with consent [7][21]" |
| Pitch 4, result screen and its Hindi sentence | depository shown as "CDSL" only | "CDSL · NSDL" (the app names the depositories actually asked; both are asked) |
| Pitch 6, "Where AI works" | "changed words and lips (forensic)" | "changed words (forensic)" (no lip analysis is built) |
| Pitch 7, key assumptions | "CDSL is live on AA for equity and fund holdings [7]; NSDL is to be confirmed" | "CDSL went live on AA in April 2023 [7]; NSDL states it is live as an FIP [21]. If either does not answer, the result is 'no record found', never 'not in your name'" |
| Architecture 3, "Limits we state openly" | "NSDL's Account Aggregator status is still to be confirmed." | Delete the sentence |
| Pitch 10, in scope | "broker and payee checks on real public lists" | "broker check on the real SEBI list; payee checks use a labelled mock of SEBI's @valid list and the I4C Suspect Registry" |
| Disclosure slide, "Models planned" | "A vision LLM ... Claude or Amazon Nova; Whisper or Amazon Transcribe; CLIP or DINOv2. Chosen at build." | "Chosen and running offline, no paid APIs: EasyOCR (Hindi and English) and Gemma 3 4B / Qwen 2.5 3B through Ollama for claim reading; faster-whisper small for speech; CLIP ViT-B/32 and perceptual hashes for source matching" |
| Pitch 7, validation targets | targets only | optionally add measured results: 300 of 300 synthetic portfolios correct; on a 64-screenshot set written by someone else, 96% of fields read right and 0 false contradictions (a development set, not a blind test); source matching 30 of 30 on development clips, consented clips pending |
| Add to the source list | | [21] NSDL, "Financial Information Provider", nsdl.com/financial-information-provider, page updated 25 Oct 2026 |

## Checked and kept

| Claim | Result | Source |
|---|---|---|
| Supreme Court upheld the Section 63(4) hash and certificate requirement, May 2026 [15] | True. *Pune Bar Association v. Union of India*, order of 22 May 2026. Note: the Court left open who must sign the Part B expert certificate, so say "certificate with the hash", not "by a notified examiner" | [SCC Online, 8 Jul 2026](https://www.scconline.com/blog/post/2026/07/08/sc-upholds-admissibility-of-electronic-evidence-under-section-63-4-bsa/) |
| Singapore: bank alerts disrupted 2,700+ live scams in two months [16] | True. Anti-Scam Centre and four banks, Jan to Feb 2024, over 2,700 scams, over S$56 million; published 6 Mar 2024 | [Singapore Police Force](https://police.gov.sg/Media-Room/News/20240306_more_than_$56_million_of_potential_losses_prevented_for_victims) |
| 77% of victims the FBI warned did not know [17] | True. DOJ elder-fraud report, Nov 2025: 6,475 victims notified as of 30 June, 77% unaware. (Earlier FBI releases said 76%, later 78%: keep the date.) | [Orrick InfoBytes, 21 Nov 2025](https://infobytes.orrick.com/2025-11-21/doj-releases-report-on-elder-fraud-and-abuse/) |
| Face-swap source can be found after JPEG compression [6] | True per the abstract (Steinebach and Götzinger, Electronic Imaging 2026, DOI 10.2352/EI.2026.38.4.MWSF-311). Only the abstract was read, so quote no accuracy figures | [IS&T library](https://library.imaging.org/ei/articles/38/4/MWSF-311) |
| CBI's ABHAY checks whether a notice is genuine [11] | True. Launched 15 May 2026 for "digital arrest" notices | [Free Press Journal](https://www.freepressjournal.in/mumbai/cbi-launches-abhay-ai-powered-notice-verification-system-to-combat-digital-arrest-scams) |
| ₹22,495 crore, over 75% investment (new Pitch 2 figure) | True. ThePrint reports 76%; 2024 was ₹22,845 crore | [ThePrint](https://theprint.in/india/cybercrime-saw-24-spike-in-2025-indians-lost-rs-22495-crore-mainly-in-investment-scams/2859930/) |
| NSDL is live on Account Aggregator | True per NSDL's own page, 14 AA partners | `data/evidence/nsdl_com_financial-information-provider.png` |
| CDSL went live on AA, April 2023 | True | `data/evidence/sahamati_org_in_depositories-as-fip-on-account-aggregator_.png` |

The old Pitch 2 figure (₹19,813 crore, 77%, IANS 3 Jan 2026) is also real, just earlier; the finale deck should use one figure only.
