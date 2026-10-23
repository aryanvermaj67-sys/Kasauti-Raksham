"""Generate synthetic holdings cases: what a (fake) trading app claims vs the mock AA depository record.

Usage: python scripts/gen_portfolios.py --n 300 --seed 42
Writes data/synthetic/portfolios/P0001.json ... Each file is MOCK data: synthetic customer, real NSE
ISINs (public list), depository accounts in the ReBIT equities v1.0.0 shape, and the expected
outcome per claimed holding. Expected labels follow from how the case is built, not from the rules.
"""

import argparse
import csv
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "synthetic" / "portfolios"
DEPOS = ["CDSL", "NSDL"]
CATEGORIES = ["fake_app_only", "mixed", "real", "no_demat", "partial_depository_failure"]


def load_isins():
    path = ROOT / "data" / "registries" / "nse_equity.csv"
    if not path.exists():
        raise SystemExit(f"{path} missing; run python scripts/fetch_registries.py first")
    with path.open(encoding="utf-8") as f:
        rows = [{k.strip(): v.strip() for k, v in r.items()} for r in csv.DictReader(f)]
    return [(r["ISIN NUMBER"], r["NAME OF COMPANY"]) for r in rows if r["SERIES"] == "EQ"]


def account(rng, i, depo, holdings):
    """One account in ReBIT equities v1.0.0 JSON shape. Transactions empty: the AA fetch asks for holdings only."""
    demat = f"1208{rng.randrange(10**11, 10**12)}0" if depo == "CDSL" else f"IN30{rng.randrange(10**9, 10**10)}0000"
    return {
        "Account": {
            "linkedAccRef": f"mock-{depo.lower()}-{i:04d}",
            "maskedDematId": "X" * (len(demat) - 4) + demat[-4:],
            "type": "equities",
            "version": "1.0.0",
            "Profile": {
                "Holders": {
                    "type": "SINGLE",
                    "Holder": [
                        {
                            "name": f"Synthetic Customer {i:04d}",
                            "dob": f"19{rng.randrange(45, 99)}-0{rng.randrange(1, 10)}-1{rng.randrange(0, 10)}",
                            "mobile": 1000000000 + i,  # deliberately not a valid Indian mobile number
                            "nominee": "REGISTERED",
                            "dematId": demat,
                            "email": f"synthetic{i:04d}@example.invalid",
                            "pan": f"ZZZPZ{i:04d}Z",
                            "kycCompliance": True,
                        }
                    ],
                }
            },
            "Summary": {
                "currentValue": round(sum(h["units"] * float(h["lastTradedPrice"]) for h in holdings), 2),
                "Investment": {"Holdings": {"type": "DEMAT", "Holding": holdings}},
            },
            "Transactions": {"startDate": "2026-04-01", "endDate": "2026-10-23", "Transaction": []},
        }
    }


def holding(rng, isin, name, units=None):
    return {
        "issuerName": name,
        "isin": isin,
        "isinDescription": f"{name.upper()} EQ",
        "units": units or rng.randrange(10, 5000),
        "lastTradedPrice": f"{rng.uniform(20, 4000):.2f}",
    }


def claim(rng, h, units=None):
    """What the fake app shows: often an inflated price."""
    qty = units or h["units"]
    return {
        "instrument_name": h["issuerName"],
        "isin": h["isin"],
        "quantity": qty,
        "value_inr": round(qty * float(h["lastTradedPrice"]) * rng.uniform(1.0, 3.0), 2),
    }


def make_case(rng, i, category, isins, failed):
    picks = rng.sample(isins, 8)
    real = [holding(rng, *p) for p in picks[:4]]  # what the depositories hold
    fake = [holding(rng, *p) for p in picks[4:]]  # shown by the app, not held anywhere
    where = {h["isin"]: rng.choice(DEPOS) for h in real}
    claims, expected = [], []

    def expect(c, outcome, reason):
        claims.append(c)
        expected.append({"isin": c["isin"], "outcome": outcome, "reason_code": reason})

    status = dict.fromkeys(DEPOS, "OK")
    if category == "fake_app_only":
        for h in fake[: rng.randrange(2, 5)]:
            expect(claim(rng, h), "CONTRADICTS", "HOLDING_NOT_FOUND_ALL_DEPOSITORIES")
    elif category == "mixed":
        for h in real[:2]:
            expect(claim(rng, h), "MATCHES", "HOLDING_FOUND")
        h = real[2]
        expect(claim(rng, h, h["units"] * rng.choice([2, 5, 10])), "CONTRADICTS", "HOLDING_QUANTITY_DIFFERS")
        for h in fake[:2]:
            expect(claim(rng, h), "CONTRADICTS", "HOLDING_NOT_FOUND_ALL_DEPOSITORIES")
    elif category == "real":
        for h in real:
            expect(claim(rng, h), "MATCHES", "HOLDING_FOUND")
    elif category == "no_demat":
        real = []
        for h in fake[:3]:
            expect(claim(rng, h), "NO_RECORD", "HOLDING_NO_DEMAT")
    else:  # partial_depository_failure: one depository FAILED, so nothing may be CONTRADICTS
        status[failed] = "FAILED"
        for h in real:
            if where[h["isin"]] != failed:
                expect(claim(rng, h), "MATCHES", "HOLDING_FOUND")
        for h in [h for h in real if where[h["isin"]] == failed] + fake[:2]:
            expect(claim(rng, h), "NO_RECORD", "HOLDING_PARTIAL_COVERAGE")

    depositories = {}
    for d in DEPOS:
        held = [h for h in real if where[h["isin"]] == d]
        accounts = [account(rng, i, d, held)] if held and status[d] == "OK" else []
        depositories[d] = {"status": status[d], "accounts": accounts}
    return {
        "mock": True,
        "case_id": f"P{i:04d}",
        "category": category,
        "failed_depository": failed,
        "customer_id": f"SYN-C{i:04d}",
        "consent_scope": DEPOS,
        "app_claims": claims,
        "portfolio_total_inr": round(sum(c["value_inr"] for c in claims), 2),
        "depositories": depositories,
        "expected": expected,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    isins = load_isins()
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("P*.json"):
        old.unlink()
    counts = {}
    for i in range(1, args.n + 1):
        category = CATEGORIES[(i - 1) % len(CATEGORIES)]
        failed = DEPOS[(i // len(CATEGORIES)) % 2] if category == "partial_depository_failure" else None
        case = make_case(rng, i, category, isins, failed)
        key = (
            f"{category} ({'CDSL ok / NSDL failed' if failed == 'NSDL' else 'NSDL ok / CDSL failed'})"
            if failed
            else category
        )
        counts[key] = counts.get(key, 0) + 1
        (OUT / f"{case['case_id']}.json").write_text(
            json.dumps(case, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    for k, v in counts.items():
        print(f"{k}: {v}")
    print(f"wrote {args.n} files to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
