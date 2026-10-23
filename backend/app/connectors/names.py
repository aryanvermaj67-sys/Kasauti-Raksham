"""Name normalisation and typo distance shared by the list connectors (ISIN master, SEBI, RBI)."""

import re

from app.constants import GENERIC_WORDS, LEGAL_WORDS


def _tokens(name: str) -> list[str]:
    return re.sub(r"[^a-z0-9 ]+", " ", name.lower().replace("&", " and ")).split()


def normalize(name: str) -> str:
    """For exact matching: lowercase, punctuation stripped, legal form (ltd, pvt, ...) dropped."""
    return " ".join(w for w in _tokens(name) if w not in LEGAL_WORDS)


def distinctive(name: str) -> str:
    """For typo matching: only the words that identify the firm; the full normalised name if none are left."""
    return " ".join(w for w in _tokens(name) if w not in GENERIC_WORDS) or normalize(name)


def within_one_edit(a: str, b: str) -> bool:
    """True if a and b are equal or one insert, delete, substitute or adjacent swap apart."""
    if a == b:
        return True
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) > len(b):
        a, b = b, a
    i = next((k for k, (x, y) in enumerate(zip(a, b, strict=False)) if x != y), len(a))
    if len(a) < len(b):
        return a[i:] == b[i + 1 :]
    return a[i + 1 :] == b[i + 1 :] or (a[i : i + 2] == b[i : i + 2][::-1] and a[i + 2 :] == b[i + 2 :])
