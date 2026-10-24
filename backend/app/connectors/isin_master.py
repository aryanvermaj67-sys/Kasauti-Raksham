"""NSE + BSE equity lists (public, cached CSV): security name -> ISIN. Exact normalised name only; never fuzzy.

A name that other listed names begin with ("Tata Motors" after the demerger, "Reliance") is ambiguous even when one
listed name equals it: the customer may hold any of them, so it is left unmapped for the customer to pick.
"""

import csv
import itertools
from functools import cache

from app.connectors import DATA, need
from app.connectors.names import normalize_security
from app.schemas.evidence import RecordResponse, make_record


@cache
def _index():
    names: dict[str, set] = {}
    reg = DATA / "registries"
    with need(reg / "nse_equity.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r = {k.strip(): v.strip() for k, v in r.items()}
            names.setdefault(normalize_security(r["NAME OF COMPANY"]), set()).add(
                (r["ISIN NUMBER"], r["NAME OF COMPANY"])
            )
    with need(reg / "bse_equity.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            for n in (r["issuer_name"], r["scrip_name"]):  # label with the scrip name: it tells ETFs apart
                names.setdefault(normalize_security(n), set()).add((r["isin"], r["scrip_name"]))
    return names


@cache
def listed_isins() -> frozenset:
    return frozenset(i for hits in _index().values() for i, _ in hits)


LOOKALIKE = {"0": "O", "O": "0", "1": "I", "I": "1", "5": "S", "S": "5", "8": "B", "B": "8", "2": "Z", "Z": "2"}


def _check_digit_ok(isin: str) -> bool:
    """ISIN check digit: letters become two digits (A=10 .. Z=35), then the Luhn test over all digits."""
    digits = [int(d) for d in "".join(str(int(c, 36)) for c in isin)]
    total = sum(d if i % 2 == 0 else (d * 2 - 9 if d > 4 else d * 2) for i, d in enumerate(reversed(digits)))
    return total % 10 == 0


def repair_isin(isin: str | None) -> str | None:
    """OCR swaps look-alike glyphs (O for 0, I for 1 ...). Return the one listed ISIN that is at most two such swaps
    away and passes the check digit; otherwise the ISIN as it was read. A listed ISIN is never changed."""
    if not isin or isin in listed_isins():
        return isin
    spots = [i for i, c in enumerate(isin) if c in LOOKALIKE]
    found = set()
    for n in (1, 2):
        for combo in itertools.combinations(spots, n):
            v = list(isin)
            for i in combo:
                v[i] = LOOKALIKE[v[i]]
            v = "".join(v)
            if v in listed_isins() and _check_digit_ok(v):
                found.add(v)
        if found:
            break  # fewer swaps is the likelier misread
    return found.pop() if len(found) == 1 else isin


def _hits(name: str) -> dict:
    """ISIN -> listed name for the exact name and for every listed name that starts with it (extra words after it)."""
    q = normalize_security(name)
    hits: dict = {}
    if not q:
        return hits
    for key, found in _index().items():
        if key == q or key.startswith(q + " "):
            hits.update(dict(found))
    return hits


def candidates(name: str) -> list[dict]:
    """Every listed security the name could mean, for the customer to pick from."""
    return [{"isin": i, "name": n} for i, n in sorted(_hits(name).items())]


def lookup(name: str, isin: str | None = None) -> RecordResponse:
    """Map a name to an ISIN, or (when the claim already shows an ISIN) say whether that ISIN is a listed one."""
    if isin:
        payload = {"query": name, "isin": isin, "matched_name": None, "candidates": 0, "listed": isin in listed_isins()}
        return make_record("isin_master", payload, mock=False)
    hits = _hits(name)
    exact = dict(_index().get(normalize_security(name), set()))
    # two ISINs under one name is ambiguous: leave it unmapped for the customer to fix
    isin, matched = next(iter(exact.items())) if len(hits) == 1 and len(exact) == 1 else (None, None)
    payload = {
        "query": name,
        "isin": isin,
        "matched_name": matched,
        "candidates": len(hits),
        "listed": isin is not None,
    }
    return make_record("isin_master", payload, mock=False)
