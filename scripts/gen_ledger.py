"""Generate a MOCK payments ledger with the FR-1.2 scam pattern injected, plus a MOCK Suspect Registry.

Usage: python scripts/gen_ledger.py [--customers 300] [--injected 40] [--seed 42]
Writes data/synthetic/ledger.json and data/synthetic/suspect_registry_mock.json.
All handles use made-up PSP suffixes (@mockupi, @validmock) so none can be a real person's UPI ID.
"""

import argparse
import json
import random
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "synthetic"
START = date(2026, 7, 1)
MERCHANTS = [
    f"{n}@mockupi"
    for n in [
        "grocer01",
        "electricity",
        "mobilerecharge",
        "pharmacy07",
        "milkdairy",
        "schoolfees",
        "gasagency",
        "kiranastore",
    ]
]
SCAM_NARRATION = [
    "IPO allotment fee",
    "trading account top-up",
    "invest in VIP stock group",
    "block deal margin",
    "withdrawal tax for profits",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--customers", type=int, default=300)
    ap.add_argument("--injected", type=int, default=40)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    customers = [f"SYN-C{i:04d}" for i in range(1, args.customers + 1)]
    txns = []

    def add(cust, day, payee, amount, narration, new_payee):
        txns.append(
            {
                "customer_id": cust,
                "date": (START + timedelta(days=day)).isoformat(),
                "payee": payee,
                "amount_inr": amount,
                "narration": narration,
                "new_payee": new_payee,
            }
        )

    for c in customers:  # ordinary spending to known payees
        for _ in range(rng.randrange(10, 30)):
            add(c, rng.randrange(0, 110), rng.choice(MERCHANTS), rng.randrange(100, 6000), "payment", False)
        if rng.random() < 0.2:  # benign decoy: a one-off large payment to a new payee
            add(
                c,
                rng.randrange(0, 110),
                f"landlord{rng.randrange(1000)}@mockupi",
                rng.randrange(8000, 40000),
                "rent",
                True,
            )
        if rng.random() < 0.1:  # legitimate broker via a @valid-format handle
            add(c, rng.randrange(0, 110), "zerobroker.brk@validmock", rng.randrange(5000, 50000), "invest SIP", True)

    injected = rng.sample(customers, args.injected)
    scam_payees = []
    # >=3 transfers to new payees within 14 days, rising amounts, invest/IPO narration, non-@valid handle
    for c in injected:
        day, amount = rng.randrange(20, 90), rng.randrange(5000, 20000)
        for _ in range(rng.randrange(3, 6)):
            payee = f"trade{rng.randrange(10000):04d}.desk@mockupi"
            scam_payees.append(payee)
            add(c, day, payee, amount, rng.choice(SCAM_NARRATION), True)
            day, amount = day + rng.randrange(1, 4), int(amount * rng.uniform(1.5, 2.5))

    txns.sort(key=lambda t: (t["date"], t["customer_id"]))
    for n, t in enumerate(txns, 1):
        t["txn_id"] = f"TXN{n:06d}"
    # demo-001's payee: a few other synthetic customers already paid it. Own seed and appended last, so every
    # row above stays identical; no invest/IPO/trading words, so only a reviewed Suspect Registry entry can warn them.
    demo = random.Random(1930)
    demo_payers = sorted(demo.sample([c for c in customers if c != "SYN-C0001"], 5))
    for c in demo_payers:
        day = START + timedelta(days=demo.randrange(60, 110))
        txns.append({"customer_id": c, "date": day.isoformat(), "payee": "zyphrastock.invest@mockupi",
                     "amount_inr": demo.randrange(10000, 90000), "narration": "Zyphra Stock Club wallet top-up",
                     "new_payee": True, "txn_id": f"TXN{len(txns) + 1:06d}"})  # fmt: skip
    OUT.mkdir(parents=True, exist_ok=True)
    ledger = {
        "mock": True,
        "note": "Synthetic payments ledger; not real bank data.",
        "injected_customers": sorted(injected),
        "demo_payee_customers": demo_payers,
        "transactions": txns,
    }
    (OUT / "ledger.json").write_text(json.dumps(ledger, indent=1) + "\n", encoding="utf-8")

    listed = sorted(set(rng.sample(scam_payees, len(scam_payees) // 2)))
    registry = {
        "mock": True,
        "note": "MOCK of the I4C Suspect Registry (the real one is shared with banks, not public).",
        "entries": [
            {
                "identifier": p,
                "type": "upi",
                "reported_count": rng.randrange(1, 12),
                "added_on": "2026-10-01",
                "source": "mock",
            }
            for p in listed
        ],
    }
    (OUT / "suspect_registry_mock.json").write_text(json.dumps(registry, indent=1) + "\n", encoding="utf-8")
    print(f"ledger: {len(txns)} transactions, {len(customers)} customers, scam pattern injected for {len(injected)}")
    print(f"suspect_registry_mock: {len(listed)} entries (mock)")
    print(f"demo payee zyphrastock.invest@mockupi paid by: {', '.join(demo_payers)}")


if __name__ == "__main__":
    main()
