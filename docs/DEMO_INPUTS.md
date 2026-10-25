# Demo inputs: what to type, what to upload, what you will see

Every row below was run through the real rules on 25 Oct 2026 (`router/check.py`, the real SEBI and RBI lists, the mock Account Aggregator, the real video comparator). "Real" means a real public record (a SEBI-registered broker, an RBI Alert List name, a listed share). "Fake" means invented here. The customers, their holdings, the UPI handles and the Suspect Registry are MOCK and synthetic: real customer data cannot be used.

## One tab with the phone and the console

Open **http://localhost:5173/present**. The customer phone is on the left and the bank reviewer console on the right, in one page (needs a window at least 1,100 px wide). The three buttons at the top, **Run demo-001 / 002 / 003**, run a real check on a demo screenshot and the console picks it up on its next refresh. **Reset demo** clears everything. Or drive the phone yourself with the inputs below and watch the console fill.

The three counters on the console, "MATCHES THE RECORD / CONTRADICTS THE RECORD / NO RECORD FOUND", count **verdicts** (one per claim) across all stored checks. To see all three move: Reset, then run demo-001 (contradicts), demo-002 (matches), demo-003 (no record).

Other links: phone alone `http://localhost:5173/app?customer=SYN-C0028`, console alone `http://localhost:5173/reviewer`. The customer in the address picks whose mock depository records are checked. Consent code: `123456`.

## 1. Holdings (type these in the "Holding" cards on the Confirm step)

| Customer in the URL | Type | You should see |
|---|---|---|
| `SYN-C0028` (real holder) | Nahar Spinning Mills Limited, quantity 3006 and Cravatex Ltd, quantity 3242 | **Matches** the record (found at CDSL) |
| `SYN-C0028` | Cravatex Ltd, quantity 5000 (the record says 3242) | **Contradicts**: different quantity |
| `SYN-C0028` (fake claim) | Reliance Industries, quantity 5000 | **Contradicts**: not in your name at CDSL and NSDL |
| `SYN-C0025` (NSDL does not answer) | MRF Limited, quantity 3368 | **Matches** (found at CDSL) |
| `SYN-C0025` | Reliance Industries, quantity 5000 | **No record**: one depository did not answer, so it can never say "not in your name" |
| any | click **Skip Holding Check (Registry Only)** on the consent step | **No record** on every holding: you did not allow the check |

More holders to type: `SYN-C0028` also holds Sintercom India Limited 4405; `SYN-C0025` holds Centum Electronics Limited 1274 and Sapphire Foods India Ltd 2181; `SYN-C0001` holds Commercial Syn Bags Ltd 722, Alfred Herbert India Ltd 270, Kilburn Engineering Ltd 1801 and IVP Ltd 4941; `SYN-C0011` holds K.P. Energy Limited 2149, Nilkamal Ltd 2184 and TD Power Systems Limited 4897. Leave the ISIN box alone: it fills itself from the share name.

## 2. Broker (the "Broker" card)

| Name | SEBI registration no. | "Says it is SEBI registered" | You should see |
|---|---|---|---|
| ZERODHA BROKING LIMITED (real) | INZ000031633 | ticked | **Matches**: on the SEBI list |
| ANGEL ONE LIMITED (real) | INZ000161534 | ticked | **Matches** (all four real rows were run) |
| Upstox Securities Private Limited (real) | INZ000315837 | ticked | **Matches** |
| GROWW INVEST TECH PRIVATE LIMITED (real) | INZ000301838 | ticked | **Matches** |
| Zyphra Stock Club (fake) | empty | ticked | **Contradicts**: not on the SEBI list |
| Zyphra Stock Club (fake) | INZ000031633 (borrowed from Zerodha) | ticked | **Contradicts**: that number belongs to another firm |
| Zerodah Broking Limited (one typo) | empty | ticked | **No record**: "not identical to the registered firm ZERODHA BROKING LIMITED" |
| Orbit Gains Desk (fake) | empty | **not** ticked | **No record**: not on the list, but it never claimed to be registered |

## 3. Payee (the "Payee" card)

| UPI ID | Account no. (last 4) | IFSC | Described as | You should see |
|---|---|---|---|---|
| zerodha.brk@validbank | empty | empty | broker | **Matches**: a SEBI @valid handle (MOCK lookup, format only) |
| fastreturns.club@mockupi | empty | empty | broker | **Contradicts**: registered brokers use @valid handles |
| trade0278.desk@mockupi | empty | empty | other | **Contradicts**: in the Suspect Registry (MOCK, one of 79 seeded entries) |
| pay.desk@mockupi | empty | empty | other | **No record**: not in the registry; who owns it is unknown |
| empty | 4821 | HDFC0001234 | other | **No record**: a bank account is not in any registry. IFSC is 4 letters, then 0, then 6 letters or digits; the account box takes only the last 4 digits |

## 4. Platform (add one with **Add Another Statement**, type Platform; tick "Says it is licensed")

| Name | Category | You should see |
|---|---|---|
| OctaFX (real name from the RBI Alert List) | forex | **Contradicts**: on the RBI Alert List of unauthorised forex platforms |
| Binomo, Exness, eToro, Alpari (real, same list, each checked) | forex | **Contradicts** |
| Zenfx Markets (fake) | forex | **No record**: not on the list. Never "safe" |

## 5. Screenshots to upload (Upload step, "Gallery")

| File | What it is | Expect |
|---|---|---|
| `data/demo_cache/demo-001.png` | fake app showing ₹3.98 crore (customer SYN-C0001) | holdings, broker and payee **contradict** |
| `data/demo_cache/demo-002.png` | a genuine holder (customer SYN-C0028) | all four holdings **match** |
| `data/demo_cache/demo-003.png` | a depository did not answer (customer SYN-C0025) | **no record** |
| `data/media/fake_apps_gemini/gm01.png` to `gm12.png` | 12 realistic English and Hindi fake-app screens (cards, table, chat, rows, ad, platform) | the reader fills the boxes in about 5 s (check them against the picture); the large-company holdings are not held by SYN-C0001, 0011, 0025 or 0028, so they **contradict** for those customers, and the invented firms are not on the SEBI list |
| `data/media/fake_apps/fa01.png` to `fa60.png` | 60 generated full-screen fake apps | same |
| any screenshot of your own | the reader is live, so any image works | check the boxes, fix what is wrong, continue |

## 6. Videos to upload (Upload step, "Video")

The index holds the 8 official recordings s01 to s08.

| File in `data/media/clips/` | What it is | You should see |
|---|---|---|
| `s05_reupload.mp4` (real) | the official clip, re-encoded | **Matches**: "the original video has the same words" |
| `s05_trimmed.mp4` (real) | the official clip, shortened | **Matches** |
| `s05_words.mp4` (fake) | the official clip with the words replaced | **Contradicts**: the original video exists, the words changed at 0:11 to 0:26, original words shown |
| `s02_words.mp4` (fake, Hindi) | same, Hindi | **Contradicts**: changed at 0:13 to 0:30 |
| `s02_lowq.mp4` (real, poor quality) | the official clip, very low quality | **No record**: "the audio matches an official recording, but the picture does not match any official footage" (found by sound only, so it never says matches) |
| `nosrc_01.mp4` to `nosrc_06.mp4` | clips that are not in the archive | **No record**: no original video found. A missing source proves nothing |

The same names exist for s01 to s08 (`_reupload`, `_trimmed`, `_cropped`, `_lowq`, `_banner`, `_words`, `_words_lowq`).

## Quick order for a full tour (3 minutes)

1. Open `/present`, click **Reset demo**.
2. Click **Run demo-001**, **Run demo-002**, **Run demo-003**: the console counters become matches, contradicts and no-record together.
3. On the phone, `?customer=SYN-C0028`: upload `demo-002.png`, confirm, consent with `123456`: matches. Then restart, type Reliance Industries 5000: contradicts.
4. Upload `s05_words.mp4` as the video: changed words found. Open the console, approve the new check: the account joins the mock Suspect Registry and other customers who paid it are listed.

## Same screenshot, three runs (all three counters from one image)

Image: `data/media/fake_apps_gemini/gm10.png` (the file `Gemini_Generated_Image_1id7qf1id7qf1id7.png` in Downloads is the same picture). Open `http://localhost:5173/app?customer=SYN-C0028`. Click **Reset demo** on `/present` first so the counters start at 0. Every row was run through the real rules.

**Do not click any of the three sample scenarios for your own image.** A sample scenario replaces your picture with its own demo screenshot (and demo-001 also attaches its own video, which is why an unrelated quote appeared in your confirm screen). Use **Gallery** for the image and **Video** for the clip. The three sample scenarios are only a shortcut to the three counters: demo-001 gives **contradicts**, demo-002 gives **matches**, demo-003 gives **no record**.

| Step | Run 1: NO RECORD | Run 2: CONTRADICTS | Run 3: MATCHES |
|---|---|---|---|
| 1. Pay | Beneficiary `gains.pay@mockupi` (the handle printed in the image). Amount `25000` | same | same |
| 2. Upload | Gallery: `gm10.png`. Video: `nosrc_01.mp4` | Gallery: `gm10.png`. Video: `s05_words.mp4` | Gallery: `gm10.png`. Video: `s05_reupload.mp4` |
| 3. Confirm: Broker card | delete it (the reader took the app name as a broker) | delete it | edit: name `ZERODHA BROKING LIMITED`, SEBI no. `INZ000031633`, tick "Says it is SEBI registered" |
| 3. Platform card | keep: `Bitora Exchange`, category `crypto` | edit: name `OctaFX`, category `forex` | delete it |
| 3. Payee card | keep: UPI `gains.pay@mockupi`, described as `other` | edit: UPI `trade0278.desk@mockupi`, described as `other` | edit: UPI `zerodha.brk@validbank`, described as `broker` |
| 3. Holdings | none | none | **Add Another Statement**, Holding: `Nahar Spinning Mills Limited`, quantity `3006`; again: `Cravatex Ltd`, quantity `3242` |
| 3. Video card | keep (person: `Teammate speaker`) | keep (person: `Teammate speaker`) | keep (person: `Teammate speaker`) |
| 4. Consent | OTP `123456`, **Authorize & Check Records** | same | same |
| Result | platform no record, payee no record, video no record (no source found) | platform contradicts (RBI Alert List), payee contradicts (Suspect Registry), video contradicts (words changed at 0:11 to 0:26) | broker matches, payee matches, both holdings match, video matches (same words) |
| Counters added | NO RECORD +3 | CONTRADICTS +3 | MATCHES +5 |

After the three runs the console reads "Verdicts in 3 stored checks": **MATCHES 5, CONTRADICTS 3, NO RECORD 3**. Run them in any order; the reviewer queue then holds three checks to approve or reject. The video outcomes were checked on the same clips; the holdings, broker, payee and platform outcomes were checked on exactly these inputs.

If you leave the stray "Broker: Bitora Exchange" card in Run 1 with "Says it is SEBI registered" ticked, it adds one **contradicts** ("not on the SEBI list"); unticked, it adds one **no record**. Delete it to keep the story clean.
