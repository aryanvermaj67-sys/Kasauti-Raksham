"""MOCK official-footage index (dev clips until the consented set exists): results of the video source check.

POST /api/video runs comparators/video.match on an upload and stores the RecordResponse here by the file's
SHA-256; the check later looks it up by the endorsement claim's media_sha256.
"""

from app.connectors import DATA
from app.schemas.evidence import RecordResponse, make_record

RESULTS = DATA / "runtime" / "video"


def store(media_sha256: str, result: dict) -> RecordResponse:
    record = make_record("footage_index", result, mock=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{media_sha256}.json").write_text(record.model_dump_json(), encoding="utf-8")
    return record


def lookup(media_sha256: str) -> RecordResponse | None:
    path = RESULTS / f"{media_sha256}.json"
    return RecordResponse.model_validate_json(path.read_text(encoding="utf-8")) if path.exists() else None
