"""Run the FR-1.2 trigger over the synthetic payments ledger and report the prompt rate.

Usage: python scripts/trigger_rate.py
Uses the committed MOCK Suspect Registry only (reviewer approvals made at runtime are left out).
"""

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app import trigger  # noqa: E402
from app.connectors import suspect_registry  # noqa: E402

if __name__ == "__main__":
    suspect_registry.ADDITIONS = ROOT / "no-runtime-additions.json"  # committed mock registry only
    ledger = json.loads((ROOT / "data" / "synthetic" / "ledger.json").read_text(encoding="utf-8"))
    customers = sorted({t["customer_id"] for t in ledger["transactions"]})
    injected = set(ledger["injected_customers"])
    prompts = {
        c: trigger.evaluate(
            [{k: t[k] for k in trigger.FIELDS} for t in ledger["transactions"] if t["customer_id"] == c]
        )
        for c in customers
    }
    prompted = {c for c, p in prompts.items() if p}
    total = sum(len(p) for p in prompts.values())
    print(f"customers: {len(customers)}; scam pattern injected for {len(injected)} (synthetic ledger, MOCK)")
    print(f"prompts: {total} (one per campaign per customer) = {1000 * total / len(customers):.0f} per 1,000 customers")
    print(f"customers prompted: {len(prompted)} = {1000 * len(prompted) / len(customers):.0f} per 1,000 customers")
    print(f"  true scam-pattern customers among them: {len(prompted & injected)} of {len(injected)} injected")
    print(f"  prompted without the injected pattern: {len(prompted - injected)}")
    print(f"prompts by reason: {dict(Counter(p['reason'] for ps in prompts.values() for p in ps))}")
