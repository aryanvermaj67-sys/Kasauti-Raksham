import hashlib
import json
import os
import tempfile
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict

from app import reader, reviewer, trigger
from app.connectors import DATA, footage_index, isin_master, suspect_registry
from app.evidence import hashchain, pack
from app.router.check import map_isins, run_check
from app.schemas.claims import ClaimSet
from app.schemas.evidence import IST
from app.schemas.verdict import CheckResult


@asynccontextmanager
async def lifespan(_app):
    print(f"retention: purged {hashchain.purge_expired()} checks older than {hashchain.RETENTION_DAYS} days")
    if os.environ.get("KASAUTI_PRELOAD_VIDEO", "1") == "1" and (ROOT / "models" / "whisper").exists():
        from app.comparators import video

        if (video.INDEX / "clips.json").exists():
            video.warm_up()
            print(f"video models ready ({video.device()})", flush=True)
    yield


app = FastAPI(title="Kasauti", lifespan=lifespan)
ROOT = DATA.parent
MAX_UPLOAD = 10 * 1024 * 1024
MAX_VIDEO = 100 * 1024 * 1024
EVENTS = DATA / "runtime" / "events.jsonl"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/read", response_model=ClaimSet)
async def api_read(file: UploadFile):
    if file.content_type not in {"image/png", "image/jpeg"}:
        raise HTTPException(415, "upload a PNG or JPG screenshot")
    data = await file.read(MAX_UPLOAD + 1)
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "file over 10 MB")
    try:
        claimset = reader.read(data)
    except LookupError as e:
        raise HTTPException(404, f"{e}; set LLM_PROVIDER=offline to read new files") from e
    except FileNotFoundError as e:
        raise HTTPException(503, str(e)) from e
    return map_isins(claimset)[0]


class CheckRequest(BaseModel):
    """claimset is the list the customer confirmed; consent_id comes from the MOCK AA consent screen."""

    model_config = ConfigDict(extra="forbid")
    claimset: ClaimSet
    customer_id: str
    consent_id: str
    consent_scope: list[Literal["CDSL", "NSDL"]] = ["CDSL", "NSDL"]


@app.post("/api/check", response_model=CheckResult)
def api_check(req: CheckRequest):
    result, records = run_check(req.claimset, req.customer_id, req.consent_id, tuple(req.consent_scope))
    hashchain.record_check(result, req.claimset, records, req.customer_id)  # FR-9: every check is chained
    return result


@app.get("/api/isin/candidates")
def api_isin_candidates(name: str):
    """Every listed security a share name could mean, so the customer can pick one (FR-2.7)."""
    return {"name": name, "candidates": isin_master.candidates(name)}


class Event(BaseModel):
    """A customer action on the result screen. Trusted contact and bank callback are MOCK: logged only."""

    model_config = ConfigDict(extra="forbid")
    kind: Literal["trusted_contact", "bank_callback", "still_pay"]
    check_id: str
    customer_id: str


@app.post("/api/events")
def api_events(event: Event):
    row = {"event_id": f"evt-{uuid.uuid4().hex[:12]}", "logged_at": datetime.now(IST).isoformat(), **event.model_dump()}
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    return {"event_id": row["event_id"], "logged_at": row["logged_at"], "mock": event.kind != "still_pay"}


@app.post("/api/video")
def api_video(file: UploadFile):
    """FR-6 source check on an uploaded clip; the result is stored as the footage_index evidence record."""
    if file.content_type not in {"video/mp4", "video/quicktime", "video/webm"}:
        raise HTTPException(415, "upload an MP4, MOV or WebM video")
    data = file.file.read(MAX_VIDEO + 1)
    if len(data) > MAX_VIDEO:
        raise HTTPException(413, "file over 100 MB")
    from app.comparators import video  # torch and the models load on the first video only

    if not (video.INDEX / "clips.json").exists():
        raise HTTPException(503, "footage index not built: run python scripts/build_footage_index.py")
    sha = hashlib.sha256(data).hexdigest()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "upload.mp4"
        path.write_bytes(data)
        result = video.match(path)
    return {"media_sha256": sha, "match": result, "record": footage_index.store(sha, result)}


def reviewer_role(x_role: str) -> str:
    """MOCK role from a header (no login in the prototype); only a reviewer may read evidence or decide."""
    if x_role != "reviewer":
        raise HTTPException(403, "reviewer role required")
    return x_role


@app.get("/api/reviewer/queue")
def api_review_queue(x_role: str = Header("customer")):
    reviewer_role(x_role)
    return reviewer.queue()


@app.get("/api/reviewer/checks/{check_id}")
def api_review_detail(check_id: str, x_role: str = Header("customer")):
    if not hashchain.checks("check_id = ?", (check_id,)):
        raise HTTPException(404, "no such check")
    return reviewer.detail(check_id, reviewer_role(x_role))


class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = ""


@app.post("/api/reviewer/checks/{check_id}/approve")
def api_review_approve(check_id: str, d: Decision, x_role: str = Header("customer")):
    return reviewer.approve(check_id, reviewer_role(x_role), d.reason)


@app.post("/api/reviewer/checks/{check_id}/reject")
def api_review_reject(check_id: str, d: Decision, x_role: str = Header("customer")):
    if not d.reason.strip():
        raise HTTPException(422, "a reason is required to reject")
    return reviewer.reject(check_id, reviewer_role(x_role), d.reason)


@app.post("/api/reviewer/checks/{check_id}/pack")
def api_review_pack(check_id: str, x_role: str = Header("customer")):
    return pack.export(check_id, reviewer_role(x_role))


@app.get("/api/registry/lookup")
def api_registry_lookup(identifier: str):
    """MOCK Suspect Registry lookup, as a bank would query it."""
    return suspect_registry.lookup(identifier)


@app.get("/api/trigger/{customer_id}")
def api_trigger(customer_id: str):
    """FR-1.2 prompts for this customer; a prompt asks for a check and never blocks a payment."""
    return {"customer_id": customer_id, "prompts": trigger.for_customer(customer_id), "payment_blocked": False}


class Ack(BaseModel):
    model_config = ConfigDict(extra="forbid")
    campaign: str


@app.post("/api/trigger/{customer_id}/ack")
def api_trigger_ack(customer_id: str, ack: Ack):
    trigger.acknowledge(customer_id, ack.campaign)
    return {"acknowledged": ack.campaign}
