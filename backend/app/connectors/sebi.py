"""SEBI registered intermediaries (public, cached CSV): brokers, investment advisers, research analysts."""

import csv
from functools import cache

from app.connectors import DATA, need
from app.connectors.names import distinctive, normalize, within_one_edit
from app.schemas.evidence import RecordResponse, make_record

LISTS = {
    "sebi_brokers.csv": "broker",
    "sebi_investment_advisers.csv": "investment_adviser",
    "sebi_research_analysts.csv": "research_analyst",
}


@cache
def _entries():
    by_name, by_reg, by_distinct = {}, {}, {}
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
                    by_distinct.setdefault(distinctive(n), e)
    return by_name, by_reg, by_distinct


def _within_one_typo(name, entry):
    """True if the name's distinctive words are within one edit of the entry's registered or trade name."""
    return any(_near(name, n) for n in {entry["name"], entry["trade_name"] or entry["name"]})


def _near(a: str, b: str) -> bool:
    """One typo in the distinctive words, or anywhere in the whole normalised name; under 3 letters never matches."""
    da, db, na, nb = distinctive(a), distinctive(b), normalize(a), normalize(b)
    return (len(da) >= 3 and within_one_edit(da, db)) or (len(na) >= 3 and within_one_edit(na, nb))


def lookup(name: str, reg_no: str | None) -> RecordResponse:
    by_name, by_reg, by_distinct = _entries()
    d = distinctive(name)
    nq = normalize(name)
    typo = (by_distinct.get(d) if len(d) >= 3 else None) or next(
        (e for k, e in by_distinct.items() if len(d) >= 3 and within_one_edit(d, k)), None
    )
    typo = typo or next((e for k, e in by_name.items() if len(nq) >= 3 and within_one_edit(nq, k)), None)
    reg = by_reg.get(reg_no.strip().upper()) if reg_no else None
    payload = {
        "query": {"name": name, "sebi_reg_no": reg_no},
        "exact": by_name.get(normalize(name)),
        "reg_no_entry": {**reg, "within_one_typo": _within_one_typo(name, reg)} if reg else None,
        "near": typo,  # a registered firm whose distinctive words are within one typo, if any
    }
    return make_record("sebi", payload, mock=False)
