"""MOCK Account Aggregator: synthetic depository holdings (CDSL, NSDL) in ReBIT equities v1.0.0 shape.

Reads data/synthetic/portfolios/*.json. One RecordResponse per depository in the consent scope, with that
depository's own OK/FAILED flag. Only the Summary (holdings) section is returned: Profile (holder PII) and
Transactions are never requested.
"""

import json
from functools import cache

from app.connectors import DATA
from app.schemas.evidence import RecordResponse, make_record

DEPOSITORIES = ("CDSL", "NSDL")


@cache
def _customers():
    out = {}
    for f in sorted((DATA / "synthetic" / "portfolios").glob("P*.json")):
        case = json.loads(f.read_text(encoding="utf-8"))
        out[case["customer_id"]] = case["depositories"]
    return out


def _summary_only(account):
    a = account["Account"]
    keep = {k: a[k] for k in ("linkedAccRef", "maskedDematId", "type", "version")}
    if "Summary" in a:
        keep["Summary"] = a["Summary"]
    return {"Account": keep}


def fetch(customer_id: str, consent_id: str, scope=DEPOSITORIES) -> list[RecordResponse]:
    depos = _customers().get(customer_id, {})  # unknown customer: no account at either depository
    out = []
    for d in scope:
        rec = depos.get(d, {"status": "OK", "accounts": []})
        if rec["status"] == "FAILED":
            payload = {"depository": d, "error": "mock depository failure flag set"}
        else:
            payload = {
                "depository": d,
                "fi_sections": ["Summary"],
                "accounts": [_summary_only(a) for a in rec["accounts"]],
            }
        out.append(make_record(f"aa_mock:{d}", payload, mock=True, consent_id=consent_id, status=rec["status"]))
    return out
