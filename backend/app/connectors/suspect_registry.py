"""MOCK of the I4C Suspect Registry (the real one is shared with banks, not public)."""

import json
from datetime import date
from functools import cache

from app.connectors import DATA
from app.schemas.evidence import RecordResponse, make_record


@cache
def _entries():
    reg = json.loads((DATA / "synthetic" / "suspect_registry_mock.json").read_text(encoding="utf-8"))
    return {e["identifier"].strip().lower(): e for e in reg["entries"]}


ADDITIONS = DATA / "runtime" / "suspect_registry_additions.json"  # MOCK writes, only after reviewer approval


def _additions() -> dict:
    return json.loads(ADDITIONS.read_text(encoding="utf-8")) if ADDITIONS.exists() else {}


def add(identifier: str, check_id: str) -> dict:
    entry = {
        "identifier": identifier,
        "type": "upi" if "@" in identifier else "account",
        "reported_count": 1,
        "added_on": date.today().isoformat(),
        "source": "mock: reviewer approval",
        "check_id": check_id,
    }
    additions = _additions() | {identifier.strip().lower(): entry}
    ADDITIONS.parent.mkdir(parents=True, exist_ok=True)
    ADDITIONS.write_text(json.dumps(additions, indent=1), encoding="utf-8")
    return entry


def lookup(identifier: str) -> RecordResponse:
    key = identifier.strip().lower()
    hit = _entries().get(key) or _additions().get(key)
    return make_record("suspect_registry", {"query": identifier, "hit": hit}, mock=True)
