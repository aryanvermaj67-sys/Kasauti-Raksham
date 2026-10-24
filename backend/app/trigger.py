"""Payment-time trigger (PRD FR-1.2 to FR-1.4). Prompts a check; never blocks a payment.

Inputs are only a customer's own transactions (date, payee, amount, narration, new-payee flag) and the MOCK
Suspect Registry. Never age, gender, language or region. One prompt per campaign per customer: a campaign is
acknowledged once and not shown again.
"""

import json
import re
from datetime import date, timedelta
from functools import cache

from app.connectors import DATA, suspect_registry, upi

FIELDS = ("txn_id", "date", "payee", "amount_inr", "narration", "new_payee")  # everything the rule may read
KEYWORDS = re.compile(r"\b(invest\w*|ipo|trading)\b", re.I)
ACKS = DATA / "runtime" / "trigger_acks.json"


@cache
def ledger() -> list[dict]:
    return json.loads((DATA / "synthetic" / "ledger.json").read_text(encoding="utf-8"))["transactions"]


def evaluate(txns) -> list[dict]:
    """FR-1.2 over one customer's transactions. Hits within 14 days of a campaign's first hit are that campaign,
    so a scam that rotates through new payees prompts once, not once per payee."""
    txns = sorted(txns, key=lambda t: t["date"])
    hits = []
    new = [t for t in txns if t["new_payee"]]
    for t in txns:
        if suspect_registry.lookup(t["payee"]).payload["hit"]:
            hits.append(("payee_in_suspect_registry", t))
        if not t["new_payee"]:
            continue
        day = date.fromisoformat(t["date"])
        window = [
            n for n in new if day - timedelta(days=14) <= date.fromisoformat(n["date"]) and n["date"] <= t["date"]
        ]
        amounts = [n["amount_inr"] for n in window]
        if len(window) >= 3 and all(a < b for a, b in zip(amounts, amounts[1:], strict=False)):
            hits.append(("rising_transfers_to_new_payees", t))
        if KEYWORDS.search(t["narration"]) and not upi.check(t["payee"]).payload["valid_handle_format"]:
            hits.append(("invest_words_without_valid_handle", t))
    campaigns = []
    for reason, t in hits:
        if campaigns and date.fromisoformat(t["date"]) - date.fromisoformat(campaigns[-1]["date"]) <= timedelta(
            days=14
        ):
            campaigns[-1]["reasons"] = sorted(set(campaigns[-1]["reasons"]) | {reason})
            continue
        campaigns.append(
            {
                "campaign": f"campaign:{t['txn_id']}",
                "reason": reason,
                "reasons": [reason],
                "payee": t["payee"],
                "txn_id": t["txn_id"],
                "date": t["date"],
            }
        )
    return campaigns


def _acks() -> dict:
    return json.loads(ACKS.read_text(encoding="utf-8")) if ACKS.exists() else {}


def for_customer(customer_id: str) -> list[dict]:
    """Prompts not yet acknowledged by this customer."""
    seen = set(_acks().get(customer_id, []))
    mine = [{k: t[k] for k in FIELDS} for t in ledger() if t["customer_id"] == customer_id]
    return [p for p in evaluate(mine) if p["campaign"] not in seen]


def acknowledge(customer_id: str, campaign: str) -> None:
    acks = _acks()
    acks.setdefault(customer_id, [])
    if campaign not in acks[customer_id]:
        acks[customer_id].append(campaign)
    ACKS.parent.mkdir(parents=True, exist_ok=True)
    ACKS.write_text(json.dumps(acks, indent=1), encoding="utf-8")


def prompt_rate() -> dict:
    """FR-1.2 prompts per 1,000 customers on the synthetic ledger: an upper bound, the scam pattern was injected."""
    txns = ledger()
    customers = sorted({t["customer_id"] for t in txns})
    prompts = sum(len(evaluate([{k: t[k] for k in FIELDS} for t in txns if t["customer_id"] == c])) for c in customers)
    return {"prompts": prompts, "customers": len(customers), "per_1000": round(1000 * prompts / len(customers))}
