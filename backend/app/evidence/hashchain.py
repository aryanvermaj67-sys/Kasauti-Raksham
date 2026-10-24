"""Evidence chain (PRD FR-9): one SHA-256 hash chain per check, stored encrypted (Fernet) in SQLite.

entry_hash = SHA-256(prev_hash + content_sha256 + kind + recorded_at); content_sha256 is over the canonical
JSON summary. Depository holdings are never stored: only the record's hash and which claimed ISINs were found.
Every read is logged with the caller's role. Evidence older than RETENTION_DAYS is purged.
"""

import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from app.comparators.holdings import compare
from app.connectors import DATA
from app.schemas.evidence import IST, canonical

DB = DATA / "runtime" / "kasauti.db"
KEY_FILE = DATA / "runtime" / "evidence.key"
RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", "30"))


def _fernet() -> Fernet:
    key = os.environ.get("EVIDENCE_KEY")
    if not key:
        # shortcut: a dev key kept next to the database; set EVIDENCE_KEY from a secret store for anything real
        if not KEY_FILE.exists():
            KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
            KEY_FILE.write_bytes(Fernet.generate_key())
        key = KEY_FILE.read_bytes().decode()
    return Fernet(key.encode() if isinstance(key, str) else key)


@contextmanager
def _db():
    """Commit on success and always close: an open handle keeps the file locked on Windows (demo reset)."""
    Path(DB).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS checks (check_id TEXT PRIMARY KEY, customer_id TEXT, created_at TEXT,
            contradicts INTEGER, status TEXT, note TEXT);
        CREATE TABLE IF NOT EXISTS entries (check_id TEXT, seq INTEGER, kind TEXT, recorded_at TEXT,
            content_sha256 TEXT, prev_hash TEXT, entry_hash TEXT, blob BLOB, PRIMARY KEY (check_id, seq));
        CREATE TABLE IF NOT EXISTS read_log (at TEXT, role TEXT, check_id TEXT, what TEXT);
    """)
    try:
        with con:
            yield con
    finally:
        con.close()


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _now() -> str:
    return datetime.now(IST).isoformat()


def append(check_id: str, kind: str, summary: dict) -> dict:
    with _db() as con:
        last = con.execute(
            "SELECT seq, entry_hash FROM entries WHERE check_id=? ORDER BY seq DESC LIMIT 1", (check_id,)
        ).fetchone()
        seq, prev = (last[0] + 1, last[1]) if last else (0, None)
        at, body = _now(), canonical(summary)
        content = _sha(body)
        entry = _sha((prev or "") + content + kind + at)
        con.execute(
            "INSERT INTO entries VALUES (?,?,?,?,?,?,?,?)",
            (check_id, seq, kind, at, content, prev, entry, _fernet().encrypt(body.encode())),
        )
    return {"seq": seq, "kind": kind, "entry_hash": entry}


def _minimal(rec, claimed: list[str], videos: list[str]) -> dict:
    """What the chain keeps of one RecordResponse."""
    base = {
        "source": rec.source,
        "fetched_at": rec.fetched_at.isoformat(),
        "consent_id": rec.consent_id,
        "status": rec.status,
        "mock": rec.mock,
        "sha256": rec.sha256,
    }
    if rec.source.startswith("aa_mock"):  # holdings are deleted after the check: keep claimed vs found ISINs only
        found = [i for i in claimed if rec.status == "OK" and compare(i, [rec])["units_found"] > 0]
        return base | {"isins_claimed": claimed, "isins_found": found}
    if rec.source == "footage_index":
        p = rec.payload
        keep = ("source_clip", "similarity", "offset_s", "changed_ranges", "transcript_same", "source_found")
        return base | {k: p.get(k) for k in keep} | {"media_sha256": videos}
    return base | {"payload": rec.payload}  # public lists and mock registries: no customer holdings


def record_check(result, claimset, records, customer_id: str) -> None:
    """Chain a finished check: the customer's files (hashed on receipt), claims, every record, the verdicts."""
    cid = result.check_id
    contradicts = any(v.outcome == "CONTRADICTS" for v in result.verdicts)
    with _db() as con:
        con.execute(
            "INSERT INTO checks VALUES (?,?,?,?,?,?)", (cid, customer_id, _now(), int(contradicts), "open", None)
        )
    videos = [c.fields.media_sha256 for c in claimset.claims if c.type == "endorsement"]
    append(cid, "artifact", {"artifact_sha256": claimset.artifact_sha256, "media_sha256": videos})
    append(cid, "claims", {"claimset": claimset.model_dump(mode="json"), "reader_fallback": claimset.reader.fallback})
    claimed = [v.params["isin"] for v in result.verdicts if v.claim_type == "holding" and v.params.get("isin")]
    for rec in records:
        append(cid, "record", _minimal(rec, claimed, videos))
    append(cid, "verdict", {"result": result.model_dump(mode="json")})


def entries(check_id: str, role: str) -> list[dict]:
    """Decrypted entries; every read is logged with the caller's role."""
    with _db() as con:
        con.execute("INSERT INTO read_log VALUES (?,?,?,?)", (_now(), role, check_id, "entries"))
        rows = con.execute(
            "SELECT seq, kind, recorded_at, content_sha256, prev_hash, entry_hash, blob FROM entries "
            "WHERE check_id=? ORDER BY seq",
            (check_id,),
        ).fetchall()
    out = []
    for seq, kind, at, content, prev, entry, blob in rows:
        try:
            summary = json.loads(_fernet().decrypt(blob))
        except InvalidToken:
            summary = {"error": "entry could not be decrypted"}
        out.append(
            {
                "seq": seq,
                "kind": kind,
                "recorded_at": at,
                "content_sha256": content,
                "prev_hash": prev,
                "entry_hash": entry,
                "summary": summary,
            }
        )
    return out


def verify_chain(check_id: str) -> tuple[bool, str]:
    """Recompute every link from the stored bytes. Any changed byte breaks it."""
    with _db() as con:
        rows = con.execute(
            "SELECT seq, kind, recorded_at, content_sha256, prev_hash, entry_hash, blob FROM entries "
            "WHERE check_id=? ORDER BY seq",
            (check_id,),
        ).fetchall()
    if not rows:
        return False, "no entries"
    prev = None
    for seq, kind, at, content, prev_hash, entry, blob in rows:
        try:
            body = _fernet().decrypt(blob).decode()
        except InvalidToken:
            return False, f"entry {seq}: ciphertext altered"
        if _sha(body) != content:
            return False, f"entry {seq}: content hash does not match"
        if prev_hash != prev:
            return False, f"entry {seq}: previous-hash link broken"
        if _sha((prev or "") + content + kind + at) != entry:
            return False, f"entry {seq}: entry hash does not match"
        prev = entry
    return True, f"chain intact: {len(rows)} entries checked"


def checks(where: str = "1=1", args=()) -> list[dict]:
    with _db() as con:
        rows = con.execute(
            f"SELECT check_id, customer_id, created_at, contradicts, status, note FROM checks WHERE {where} "
            "ORDER BY created_at DESC",
            args,
        ).fetchall()
    keys = ("check_id", "customer_id", "created_at", "contradicts", "status", "note")
    return [dict(zip(keys, r, strict=True)) for r in rows]


def set_status(check_id: str, status: str, note: str | None) -> None:
    with _db() as con:
        con.execute("UPDATE checks SET status=?, note=? WHERE check_id=?", (status, note, check_id))


def purge_expired(now: datetime | None = None, days: int = RETENTION_DAYS) -> int:
    """Retention (FR-9.4): delete checks and their evidence older than `days`."""
    cutoff = ((now or datetime.now(IST)) - timedelta(days=days)).isoformat()
    with _db() as con:
        old = [r[0] for r in con.execute("SELECT check_id FROM checks WHERE created_at < ?", (cutoff,))]
        for cid in old:
            con.execute("DELETE FROM entries WHERE check_id=?", (cid,))
            con.execute("DELETE FROM checks WHERE check_id=?", (cid,))
    return len(old)
