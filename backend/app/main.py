import json
import uuid
from datetime import datetime
from typing import Literal

from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict

from app import reader
from app.connectors import DATA, isin_master
from app.router.check import map_isins, run_check
from app.schemas.claims import ClaimSet
from app.schemas.evidence import IST
from app.schemas.verdict import CheckResult

app = FastAPI(title="Kasauti")
MAX_UPLOAD = 10 * 1024 * 1024
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
    return run_check(req.claimset, req.customer_id, req.consent_id, tuple(req.consent_scope))[0]


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
