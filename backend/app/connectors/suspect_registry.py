"""MOCK of the I4C Suspect Registry (the real one is shared with banks, not public)."""

import json
from functools import cache

from app.connectors import DATA
from app.schemas.evidence import RecordResponse, make_record


@cache
def _entries():
    reg = json.loads((DATA / "synthetic" / "suspect_registry_mock.json").read_text(encoding="utf-8"))
    return {e["identifier"].strip().lower(): e for e in reg["entries"]}


def lookup(identifier: str) -> RecordResponse:
    hit = _entries().get(identifier.strip().lower())
    return make_record("suspect_registry", {"query": identifier, "hit": hit}, mock=True)
