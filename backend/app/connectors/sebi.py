"""SEBI registered intermediaries (public, cached CSV): brokers, investment advisers, research analysts."""

import csv
import difflib
from functools import cache

from app.connectors import DATA, need
from app.connectors.names import normalize
from app.schemas.evidence import RecordResponse, make_record

LISTS = {
    "sebi_brokers.csv": "broker",
    "sebi_investment_advisers.csv": "investment_adviser",
    "sebi_research_analysts.csv": "research_analyst",
}


@cache
def _entries():
    by_name, by_reg = {}, {}
    for file, kind in LISTS.items():
        with need(DATA / "registries" / file).open(encoding="utf-8") as f:
            for r in csv.DictReader(f):
                e = {
                    "name": r["Name"],
                    "trade_name": r.get("Trade Name") or None,
                    "reg_no": r["Registration No."].strip().upper(),
                    "list": kind,
                }
                by_reg[e["reg_no"]] = e
                for n in {r["Name"], r.get("Trade Name") or r["Name"]}:
                    by_name.setdefault(normalize(n), e)
    return by_name, by_reg


def lookup(name: str, reg_no: str | None) -> RecordResponse:
    by_name, by_reg = _entries()
    q = normalize(name)
    near = difflib.get_close_matches(q, by_name.keys(), n=1, cutoff=0.6)
    sim = round(difflib.SequenceMatcher(None, q, near[0]).ratio(), 3) if near else None
    payload = {
        "query": {"name": name, "sebi_reg_no": reg_no},
        "exact": by_name.get(q),
        "reg_no_entry": by_reg.get(reg_no.strip().upper()) if reg_no else None,
        "near": {**by_name[near[0]], "similarity": sim} if near else None,
    }
    return make_record("sebi", payload, mock=False)
