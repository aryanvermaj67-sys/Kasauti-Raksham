"""Broker-matching evaluation on the real cached SEBI broker list (fixed seed).

Usage: python scripts/broker_match_eval.py [--seed 7]
Four sets of 50, each run through sebi.lookup + rules.broker (claims_registered=True, no reg no):
  a) invented: one made-up word plus generic words; the word is at least two edits from every
     registered firm's distinctive words (one edit away would be set b)  -> all CONTRADICTS
  b) typo: real name, one letter substituted in its longest distinctive word (4+ letters)
                                                         -> no MATCHES, >= 90% NO_RECORD
  c) variant: real name with only case, punctuation, Ltd/Limited, Pvt/Private changed -> all MATCHES
  d) exact: real names as listed                         -> all MATCHES
Prints a confusion table and every name that misses its target. Exit 1 on any miss.
"""

import argparse
import csv
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.connectors import sebi  # noqa: E402
from app.constants import GENERIC_WORDS  # noqa: E402
from app.schemas.claims import BrokerClaim  # noqa: E402
from app.verdict import rules  # noqa: E402

OUTCOMES = ["MATCHES", "NO_RECORD", "CONTRADICTS"]
GENERIC_FOR_NAMES = [
    "Capital",
    "Wealth",
    "Securities",
    "Broking",
    "Stock",
    "Club",
    "Finance",
    "Investments",
    "Advisors",
]
CONSONANTS, VOWELS = "bcdfghjklmnprstvwxyz", "aeiou"


def outcome(name):
    c = BrokerClaim(id="c1", type="broker", fields={"name": name, "sebi_reg_no": None, "claims_registered": True})
    return rules.broker(c, sebi.lookup(name, None)).outcome


def osa_distance(a, b):
    """Edit distance with adjacent swaps (optimal string alignment); independent of the rule's own check."""
    d = [[i + j if not i * j else 0 for j in range(len(b) + 1)] for i in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] != b[j - 1]))
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[-1][-1]


def invented(rng, registered):
    while True:
        word = "".join(rng.choice(CONSONANTS) + rng.choice(VOWELS) for _ in range(rng.randint(2, 4)))
        near = (k for k in registered if abs(len(k) - len(word)) < 2 and osa_distance(word, k) < 2)
        if word not in GENERIC_WORDS and next(near, None) is None:
            return f"{word.title()} {' '.join(rng.sample(GENERIC_FOR_NAMES, rng.randint(1, 2)))}"


def typo(rng, name):
    words = [w for w in re.findall(r"[A-Za-z]+", name) if len(w) >= 4 and w.lower() not in GENERIC_WORDS]
    target = max(words, key=len)
    i = rng.randrange(len(target))
    new = rng.choice([c for c in "abcdefghijklmnopqrstuvwxyz" if c != target[i].lower()])
    new = new.upper() if target[i].isupper() else new
    return name.replace(target, target[:i] + new + target[i + 1 :], 1)


def variant(rng, name):
    v = (
        re.sub(r"\bLIMITED\b", "Ltd.", name, flags=re.I)
        if re.search(r"\bLIMITED\b", name, re.I)
        else re.sub(r"\bLTD\b\.?", "Limited", name, flags=re.I)
    )
    v = re.sub(r"\bPRIVATE\b", "Pvt.", v, flags=re.I) if rng.random() < 0.5 else v
    v = v.replace(",", "") if "," in v else v.replace(" Ltd.", ", Ltd.")
    return rng.choice([str.lower, str.upper, str.title])(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    seed = ap.parse_args().seed
    rng = random.Random(seed)
    with (ROOT / "data" / "registries" / "sebi_brokers.csv").open(encoding="utf-8") as f:
        names = sorted({r["Name"].strip() for r in csv.DictReader(f)})
    registered = list(sebi._entries()[2])  # distinctive words of every SEBI-listed firm the rule checks against
    typo_pool = [
        n for n in names if any(len(w) >= 4 and w.lower() not in GENERIC_WORDS for w in re.findall(r"[A-Za-z]+", n))
    ]
    legal_pool = [n for n in names if re.search(r"\b(LIMITED|LTD)\b", n, re.I)]
    sets = {
        "a invented": [invented(rng, registered) for _ in range(50)],
        "b typo": [typo(rng, n) for n in rng.sample(typo_pool, 50)],
        "c variant": [variant(rng, n) for n in rng.sample(legal_pool, 50)],
        "d exact": rng.sample(names, 50),
    }
    targets = {
        "a invented": lambda c: c["CONTRADICTS"] == 50,
        "b typo": lambda c: c["MATCHES"] == 0 and c["NO_RECORD"] >= 45,
        "c variant": lambda c: c["MATCHES"] == 50,
        "d exact": lambda c: c["MATCHES"] == 50,
    }
    wanted = {"a invented": "CONTRADICTS", "b typo": "NO_RECORD", "c variant": "MATCHES", "d exact": "MATCHES"}
    print(f"seed {seed}, {len(names)} SEBI broker names")
    print(f"{'set':12} {'MATCHES':>8} {'NO_RECORD':>10} {'CONTRADICTS':>12}  target")
    failed = []
    for label, sample in sets.items():
        got = {n: outcome(n) for n in sample}
        counts = {o: sum(v == o for v in got.values()) for o in OUTCOMES}
        ok = targets[label](counts)
        row = f"{counts['MATCHES']:>8} {counts['NO_RECORD']:>10} {counts['CONTRADICTS']:>12}"
        print(f"{label:12} {row}  {'met' if ok else 'MISSED'}")
        if not ok:
            failed += [f"  {label}: {n!r} -> {o}" for n, o in got.items() if o != wanted[label]]
    demo = outcome("Zyphra Stock Club")
    print(f"Zyphra Stock Club -> {demo}")
    if demo != "CONTRADICTS":
        failed.append("  demo broker Zyphra Stock Club is not CONTRADICTS")
    print("\n".join(failed) if failed else "all targets met")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
