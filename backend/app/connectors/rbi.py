"""RBI Alert List of unauthorised forex platforms (public; hand-typed from the PDF, see data/SOURCES.md)."""

import csv
import re
from functools import cache

from app.connectors import DATA, need
from app.connectors.names import normalize
from app.schemas.evidence import RecordResponse, make_record


@cache
def _index():
    out = {}
    with need(DATA / "registries" / "rbi_alert_list.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[normalize(r["name"])] = r
            domain = re.sub(r"^(https?://)?(www\.)?", "", r.get("website") or "").split("/")[0].split(".")[0]
            if domain:
                out.setdefault(normalize(domain), r)
    return out


def lookup(name: str) -> RecordResponse:
    return make_record("rbi", {"query": name, "match": _index().get(normalize(name))}, mock=False)
