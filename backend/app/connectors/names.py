"""Name normalisation shared by the list connectors (ISIN master, SEBI, RBI)."""

import re

DROP = {"limited", "ltd", "pvt", "private", "the", "co", "inc", "llp"}


def normalize(name: str) -> str:
    words = re.sub(r"[^a-z0-9 ]+", " ", name.lower().replace("&", " and ")).split()
    return " ".join(w for w in words if w not in DROP)
