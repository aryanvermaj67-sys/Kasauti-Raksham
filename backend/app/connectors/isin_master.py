"""NSE + BSE equity lists (public, cached CSV): instrument name -> ISIN. Exact normalised name only."""

import csv
from functools import cache

from app.connectors import DATA, need
from app.connectors.names import normalize
from app.schemas.evidence import RecordResponse, make_record


@cache
def _index():
    names: dict[str, set] = {}
    reg = DATA / "registries"
    with need(reg / "nse_equity.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r = {k.strip(): v.strip() for k, v in r.items()}
            if r["SERIES"] == "EQ":
                names.setdefault(normalize(r["NAME OF COMPANY"]), set()).add((r["ISIN NUMBER"], r["NAME OF COMPANY"]))
    with need(reg / "bse_equity.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            for n in (r["issuer_name"], r["scrip_name"]):
                names.setdefault(normalize(n), set()).add((r["isin"], r["issuer_name"]))
    return names


def lookup(name: str) -> RecordResponse:
    hits = dict(_index().get(normalize(name), set()))
    # two ISINs under one name is ambiguous: leave it unmapped for the customer to fix
    isin, matched = next(iter(hits.items())) if len(hits) == 1 else (None, None)
    payload = {"query": name, "isin": isin, "matched_name": matched, "candidates": len(hits)}
    return make_record("isin_master", payload, mock=False)
