"""Reviewer console logic (FR-10). One customer's report never lists an account; a reviewer's approval does."""

from statistics import median
from typing import get_args

from app import trigger
from app.connectors import suspect_registry
from app.evidence import hashchain
from app.schemas.verdict import Outcome
from app.trigger import ledger


def queue() -> list[dict]:
    return hashchain.checks("contradicts = 1 AND status = 'open'")


def detail(check_id: str, role: str) -> dict:
    entries = hashchain.entries(check_id, role)
    ok, why = hashchain.verify_chain(check_id)
    by_kind = {e["kind"]: e["summary"] for e in entries}
    return {
        "check": hashchain.checks("check_id = ?", (check_id,))[0],
        "claims": by_kind.get("claims", {}).get("claimset", {}).get("claims", []),
        "result": by_kind.get("verdict", {}).get("result"),
        "records": [e["summary"] for e in entries if e["kind"] == "record"],
        "hashes": [
            {k: e[k] for k in ("seq", "kind", "recorded_at", "content_sha256", "prev_hash", "entry_hash")}
            for e in entries
        ],
        "chain": {"valid": ok, "detail": why},
        "network": [  # MOCK sources only: the Suspect Registry mock and the synthetic payments ledger
            {
                "payee": p,
                "registry_hit": suspect_registry.lookup(p).payload["hit"],
                "ledger_payers": sorted({t["customer_id"] for t in ledger() if t["payee"] == p}),
            }
            for p in _payees({"claims": by_kind.get("claims", {}).get("claimset", {}).get("claims", [])})
        ],
    }


def _payees(d: dict) -> list[str]:
    out = []
    for c in d["claims"]:
        f = c["fields"]
        if c["type"] == "payee":
            out.append(f["upi_id"] or f"XXXX{f['account_no_last4'] or ''}" + (f" ({f['ifsc']})" if f["ifsc"] else ""))
    return out


def approve(check_id: str, role: str, note: str = "") -> dict:
    d = detail(check_id, role)
    customer = d["check"]["customer_id"]
    added = [suspect_registry.add(p, check_id) for p in _payees(d)]
    others = sorted({t["customer_id"] for t in ledger() for a in added if t["payee"] == a["identifier"]} - {customer})
    hashchain.append(
        check_id,
        "review",
        {
            "decision": "approved",
            "role": role,
            "note": note,
            "registry_added": [a["identifier"] for a in added],
            "other_payers": others,
        },
    )
    hashchain.set_status(check_id, "approved", note)
    return {"check_id": check_id, "registry_added": added, "other_customers_who_paid": others}


def reject(check_id: str, role: str, reason: str) -> dict:
    hashchain.append(check_id, "review", {"decision": "rejected", "role": role, "reason": reason})
    hashchain.set_status(check_id, "rejected", reason)
    return {"check_id": check_id, "status": "rejected", "reason": reason}


STATES = ("new", "in_review", "approved", "rejected")


def cases() -> dict:
    """Every reported check (one with a CONTRADICTS verdict), by review state; "in_review" = a reviewer opened it."""
    opened = hashchain.read_by("reviewer")
    out = {s: [] for s in STATES}
    for c in hashchain.checks("contradicts = 1"):
        state = c["status"] if c["status"] != "open" else ("in_review" if c["check_id"] in opened else "new")
        out[state].append(c)
    return out


def stats(role: str) -> dict:
    """Computed from the evidence store, never typed in: outcome counts, median latency, and the prompt rate."""
    rows = hashchain.verdict_summaries(role)
    outcomes = dict.fromkeys(get_args(Outcome), 0)  # the schema's three outcomes, counted
    for r in rows:
        for v in r["result"]["verdicts"]:
            outcomes[v["outcome"]] += 1
    lat = [r["latency_s"] for r in rows if r.get("latency_s") is not None]
    return {
        "checks": len(rows),
        "outcomes": outcomes,
        "median_latency_s": round(median(lat), 2) if lat else None,
        "latency_samples": len(lat),
        "prompt_rate": trigger.prompt_rate(),
    }
