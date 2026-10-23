"""Name-to-ISIN collision check over the full cached NSE and BSE equity lists.

Usage: python scripts/isin_collisions.py
Prints how many securities and distinct normalised names there are, every pair of different ISINs that
normalise to the same name (first 20 listed), and every listed name that does not map back to its own ISIN.
An ambiguous name must map to no ISIN (the holding becomes NO_RECORD); exit 1 if any name maps to a wrong ISIN
or the demo-001 holdings do not map to their ISINs.
"""

import csv
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.connectors import isin_master  # noqa: E402
from app.connectors.names import normalize_security  # noqa: E402

DEMO = {"Reliance Industries": "INE002A01018", "Tata Consultancy Services": "INE467B01029", "Infosys": "INE009A01021"}


def listed_names():
    reg = ROOT / "data" / "registries"
    rows = []
    with (reg / "nse_equity.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r = {k.strip(): v.strip() for k, v in r.items()}
            rows.append(("NSE", r["NAME OF COMPANY"], r["ISIN NUMBER"]))
    with (reg / "bse_equity.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows += [("BSE", r["issuer_name"], r["isin"]), ("BSE", r["scrip_name"], r["isin"])]
    return rows


def main():
    rows = listed_names()
    by_name, names_of = defaultdict(set), defaultdict(set)
    for _, name, isin in rows:
        by_name[normalize_security(name)].add(isin)
        names_of[isin].add(name)
    pairs = [
        (n, a, b) for n, isins in sorted(by_name.items()) if len(isins) > 1 for a, b in combinations(sorted(isins), 2)
    ]
    print(
        f"securities: {len({i for *_, i in rows})} distinct ISINs ({len(rows)} listed names)"
    )
    print(f"distinct normalised names: {len(by_name)}")
    print(f"different-ISIN pairs with the same normalised name: {len(pairs)}")
    for n, a, b in pairs[:20]:
        print(f"  {n!r}: {a} {sorted(names_of[a])} | {b} {sorted(names_of[b])}")

    ambiguous, wrong = [], []
    for exchange, name, isin in rows:
        got = isin_master.lookup(name).payload
        if got["isin"] == isin:
            continue
        (ambiguous if got["isin"] is None and got["candidates"] > 1 else wrong).append((exchange, name, isin, got))
    print(f"names that do not map back to their own ISIN: {len(ambiguous) + len(wrong)}")
    for exchange, name, isin, got in ambiguous:
        print(f"  ambiguous -> no ISIN (holding is NO_RECORD): {exchange} {name!r} ({isin}), {got['candidates']} ISINs")
    for exchange, name, isin, got in wrong:
        print(f"  WRONG: {exchange} {name!r} ({isin}) -> {got['isin']}")
    demo = {n: isin_master.lookup(n).payload["isin"] for n in DEMO}
    print(f"demo-001 holdings: {demo} -> {'ok' if demo == DEMO else 'WRONG'}")
    return 1 if wrong or demo != DEMO else 0


if __name__ == "__main__":
    sys.exit(main())
