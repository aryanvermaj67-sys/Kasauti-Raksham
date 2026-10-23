"""RecordResponse and EvidencePack. Mirror docs/formats/record_response.schema.json and evidence_pack.schema.json."""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
IST = timezone(timedelta(hours=5, minutes=30))


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RecordResponse(Strict):
    source: str = Field(pattern=r"^(aa_mock:(CDSL|NSDL)|isin_master|sebi|rbi|upi|suspect_registry|footage_index)$")
    fetched_at: datetime
    consent_id: str | None
    status: Literal["OK", "FAILED"]
    mock: bool
    payload: dict[str, Any]
    sha256: Sha256


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def make_record(source, payload, *, mock, consent_id=None, status="OK") -> RecordResponse:
    return RecordResponse(
        source=source,
        fetched_at=datetime.now(IST),
        consent_id=consent_id,
        status=status,
        mock=mock,
        payload=payload,
        sha256=hashlib.sha256(canonical(payload).encode()).hexdigest(),
    )


class EvidenceEntry(Strict):
    seq: int = Field(ge=0)
    kind: Literal["artifact", "claims", "record", "verdict", "event", "review"]
    recorded_at: datetime
    content_sha256: Sha256
    prev_hash: Sha256 | None
    entry_hash: Sha256
    summary: dict[str, Any]


class EvidencePack(Strict):
    pack_id: str
    check_id: str
    exported_at: datetime
    chain_valid: bool
    entries: Annotated[list[EvidenceEntry], Field(min_length=1)]
