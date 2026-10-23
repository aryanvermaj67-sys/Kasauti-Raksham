"""SEBI @valid UPI handle: FORMAT RULE ONLY. SEBI Check is a lookup tool, not a dataset, so ownership is a MOCK."""

import re

from app.schemas.evidence import RecordResponse, make_record

# shortcut: only the .brk (broker) and .mf (mutual fund) categories are encoded; add others once confirmed from SEBI
VALID = re.compile(r"[a-z0-9]+(\.[a-z0-9]+)*\.(brk|mf)@valid[a-z]+")


def check(upi_id: str) -> RecordResponse:
    q = upi_id.strip()
    valid = q.isascii() and bool(VALID.fullmatch(q.lower()))  # isascii: look-alike letters never pass
    return make_record("upi", {"query": upi_id, "valid_handle_format": valid}, mock=True)
