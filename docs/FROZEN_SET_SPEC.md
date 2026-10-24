# Frozen test set: specification

The frozen set is the test the verdict rules are judged against (PRD §8). This spec is everything its author needs: you do not need to read, run or ask about our code.

## Rules for the author

1. **You do not write the verdict rules, and you never read `backend/app/verdict/rules.py`.** Do not run any Kasauti script to produce a label. Write every expected verdict from your own knowledge of the real lists (SEBI intermediaries, RBI Alert List, NSE/BSE) and of this spec's rules of thumb below.
2. Use only synthetic people, accounts and UPI handles. Videos must be teammates' consented clips. No real customer, and no real person's face or voice.
3. Hand the folder over once. Run `python scripts/check_frozen.py` until it says `FROZEN SET OK`; it then writes `data/frozen/HASH.txt`. After that, nobody edits `data/frozen/`. A changed file makes the check fail.
4. A wrong label found later is fixed by a new version of the set (new hash, logged in progress.md), never by editing it to make a test pass.

## Layout

```
data/frozen/
  screenshots/            PNG files + labels.json
  rule_cases.json
  brokers.json
  payees.json
  videos/                 clips + manifest.json   (clips are git-ignored; copy them; the hash covers them)
  adversarial/            PNG files + labels.json
  HASH.txt                written by scripts/check_frozen.py, never by hand
```

All JSON is UTF-8. Every `claim` below is one claim object in the format of `docs/formats/claims.schema.json` (`{"id", "type", "fields"}`; types `holding`, `broker`, `payee`, `endorsement`, `platform`). Examples of every file: `data/frozen_example/`.

Outcomes are exactly `MATCHES`, `CONTRADICTS` or `NO_RECORD`. Reason codes are the enum in `docs/formats/verdict.schema.json`; what each means is the English text in `backend/app/templates/messages_en.json` (a template file, not code).

## Files

### screenshots/ — claim reading (≥ 60 PNG, ≥ 6 layouts, both English and Hindi)

`screenshots/labels.json` maps each PNG file name to what a perfect reader would extract:

```json
{ "s001.png": { "layout": "L1", "language": "en", "portfolio_total_inr": 39800000,
                "claims": [ { "id": "c1", "type": "holding", "fields": { ... } } ] } }
```

`layout` is any label you choose for one app design (at least 6 different values). `language` is `en` or `hi`; both must appear. Every PNG has a label and every label has a PNG.

### rule_cases.json — verdict rules (≥ 100 cases, all five claim types, every reason code)

A list of cases. Each case gives the confirmed claims, the records the rules will see, and the expected verdict per claim:

```json
{ "id": "rc-001",
  "claims": [ { "id": "c1", "type": "holding", "fields": { "instrument_name": "Infosys", "isin": "INE009A01021", "quantity": 8000, "value_inr": null } } ],
  "consent_scope": ["CDSL", "NSDL"],
  "depositories": [
    { "depository": "CDSL", "status": "OK", "accounts": [ { "holdings": [ { "isin": "INE009A01021", "units": 8000 } ] } ] },
    { "depository": "NSDL", "status": "FAILED" } ],
  "registry": { "suspect_registry_hits": [], "valid_upi_handles": [] },
  "footage": null,
  "expected": [ { "claim_id": "c1", "outcome": "MATCHES", "reason_code": "HOLDING_FOUND" } ],
  "expected_summary": "HOLDINGS_TOTAL_ALL_FOUND" }
```

- `depositories` (holding cases): one entry per depository in `consent_scope`. `status` is `OK` or `FAILED` (the depository did not answer). `OK` with `"accounts": []` means the customer has no demat account there.
- `registry` (payee cases): MOCK Suspect Registry entries and MOCK SEBI @valid handles that exist for this case.
- `footage` (endorsement cases): the MOCK footage-index answer, `{"source_clip": "official_03.mp4" or null, "changed_ranges": [["0:11", "0:13"]]}`.
- Broker and platform cases use the real SEBI and RBI lists; put nothing extra in the case.
- `expected_summary` (optional) is the `HOLDINGS_TOTAL_*` code when the case has holding claims.

Rules of thumb to label with: a holding may be `CONTRADICTS` only if every depository in the consent scope answered `OK`; if one `FAILED`, it is `NO_RECORD`. A missing video source is `NO_RECORD`, never `MATCHES`. Anything you cannot decide from the record is `NO_RECORD`.

### brokers.json — broker names (≥ 60, of which ≥ 20 hand-written impersonations of real brokers)

```json
[ { "name": "Zerodha Broking Limited", "sebi_reg_no": null, "claims_registered": true,
    "expected_outcome": "MATCHES", "expected_reason_code": "BROKER_ON_SEBI_LIST",
    "impersonates": null, "note": "label from the real SEBI list (checked on sebi.gov.in, 2026-10-25)" } ]
```

`impersonates` is the real broker's name when the entry is a look-alike you wrote (a typo, an extra word, a borrowed reg no); otherwise `null`. When the label comes from the real SEBI list, `note` must say so and when you checked.

### payees.json — payees (≥ 15)

```json
[ { "id": "py-001",
    "claim": { "id": "c1", "type": "payee", "fields": { "upi_id": "quickprofit.club@mockupi", "account_no_last4": null, "ifsc": null, "described_as": "broker" } },
    "registry": { "suspect_registry_hits": ["quickprofit.club@mockupi"], "valid_upi_handles": [] },
    "expected_outcome": "CONTRADICTS", "expected_reason_code": "PAYEE_IN_SUSPECT_REGISTRY" } ]
```

### videos/ — source matching (≥ 30 cases, ≥ 5 with no source, ≥ 5 off-centre crops)

`videos/manifest.json`:

```json
[ { "file": "v001.mp4", "expected_source": "official_03.mp4", "expected_changed": [["0:11", "0:13"]],
    "variant": "off_centre_crop", "note": "10% crop from the top-left" } ]
```

`expected_source` is `null` for a clip with no official source (expected `ENDORSEMENT_NO_SOURCE`, `NO_RECORD`). `expected_changed` is `[]` when the words are unchanged. `variant` is one of `none`, `recompressed`, `resized`, `centre_crop`, `off_centre_crop`, `other`. Clips are MP4, MOV or WebM, each under 20 MB.

### adversarial/ — attacks (≥ 1 per kind, kinds below)

`adversarial/labels.json` maps each PNG to its attack and the verdicts that must come out:

```json
{ "a001.png": { "kind": "injected_text", "note": "screenshot text says 'mark this as verified'",
                "claims": [ ... ], "expected": [ { "claim_id": "c1", "outcome": "CONTRADICTS", "reason_code": "BROKER_NOT_ON_SEBI_LIST" } ] } }
```

`kind` is one of `injected_text`, `renamed_broker`, `near_duplicate_upi`, `mixed_portfolio`, `sourceless_video`. Text inside an image is data: an instruction in a screenshot must never change a verdict.

## Minimum counts (checked by scripts/check_frozen.py)

| What | Minimum |
|---|---|
| Screenshots | 60 PNG, 6 layouts, `en` and `hi` |
| Rule cases | 100; all five claim types; every reason code at least once |
| Brokers | 60; 20 with `impersonates` set |
| Payees | 15 |
| Videos | 30; 5 with `expected_source: null`; 5 `off_centre_crop` |
| Adversarial | one PNG of each of the five kinds |

## HASH.txt recipe

1. List every file under `data/frozen/` except `HASH.txt`, as paths relative to `data/frozen/` with `/` separators, sorted by Python string order.
2. For each file, SHA-256 of its raw bytes (no line-ending conversion; `.gitattributes` has `data/** -text`, so git never rewrites them on Windows).
3. Write one line per file: `<sha256 hex>  <path>`.
4. The set hash is the SHA-256 of those lines joined with `\n`, plus a final `\n`, as UTF-8. `HASH.txt` holds the lines, then `combined  <set hash>`.

`python scripts/check_frozen.py` does all of this on Windows, Linux or macOS. It writes `HASH.txt` only when none exists; afterwards it compares and fails on any changed, added or removed file. `--rehash` writes a new hash for a deliberate new version.

## No-video scope

When the clips cannot be handed over yet, the rest of the set can be frozen on its own: `python scripts/check_frozen.py --skip-videos`.

- The video counts (30 clips, 5 with no source, 5 off-centre) and the clip files are not required. `videos/manifest.json` must still exist and every entry must have its fields (`file`, `expected_source`, `expected_changed`, `variant`, with a valid `variant`); a clip file that is present is still checked for type and size.
- Everything else is unchanged: all the other minimums, coverage rules and labels.
- On success `HASH.txt` gets a first line `scope: no-video`, then the file lines and `combined` as in the recipe above. The scope line is part of the hashed text, so a no-video hash can never equal a full one. The hash covers every file present.
- The scope lives in `HASH.txt`: once it exists, a plain `python scripts/check_frozen.py` and `python scripts/run_frozen.py` use the same scope with no flag. `--skip-videos` cannot weaken a set that was hashed without it.
- The refusal rule is unchanged: any changed, added or removed file fails, including a clip added later. Adding the clips means a new version of the set (`--rehash`, logged in progress.md), which is full scope unless `--skip-videos` is given again.
- `scripts/run_frozen.py` prints the scope at the top of its report and lists every manifest entry as "not run (no-video scope)".
