import hashlib
import json
import os
import tempfile
import threading
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
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
    jobs = []
    if os.environ.get("KASAUTI_PRELOAD_VIDEO", "1") == "1" and (ROOT / "models" / "whisper").exists():
        from app.comparators import video

        if (video.INDEX / "audio.npz").exists():
            jobs.append(("video models", lambda: (video.warm_up(), print(f"video models ready ({video.device()})"))))
    if os.environ.get("LLM_PROVIDER", "local") == "local":  # EasyOCR + the first Ollama call are slow
        jobs.append(("claim reader", reader.local.warm_up))
    LOADING.update(name for name, _ in jobs)
    threading.Thread(target=_warm_up, args=(jobs,), daemon=True).start()  # /health says ready=false until done
    yield


LOADING: set[str] = set()


def _warm_up(jobs) -> None:
    for name, load in jobs:  # one at a time: CLIP, Whisper and Ollama share one GPU
        try:
            load()
        except Exception as e:  # a model that fails to load must not leave the UI "preparing" forever
            print(f"{name} warm-up failed: {e}", flush=True)
        finally:
            LOADING.discard(name)


app = FastAPI(title="Kasauti", lifespan=lifespan)
ROOT = DATA.parent
MAX_UPLOAD = 10 * 1024 * 1024
MAX_VIDEO = 100 * 1024 * 1024
EVENTS = DATA / "runtime" / "events.jsonl"


@app.get("/health")
@app.get("/api/health")  # the frontend dev proxy forwards /api only
def health():
    return {"status": "ok", "ready": not LOADING, "loading": sorted(LOADING)}


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
    t0 = time.perf_counter()
    result, records = run_check(req.claimset, req.customer_id, req.consent_id, tuple(req.consent_scope))
    # FR-9: every check is chained; the latency (records + rules) feeds GET /stats
    hashchain.record_check(result, req.claimset, records, req.customer_id, round(time.perf_counter() - t0, 3))
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

    if not (video.INDEX / "audio.npz").exists():  # absent in an index built before the audio checks
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


DEMO = DATA / "demo_cache"


def _scenarios() -> list[dict]:
    """The demo artifacts in the repo: screenshot, its synthetic customer, the dev clip for it (if present)."""
    customers = json.loads((DEMO / "demo_customers.json").read_text(encoding="utf-8"))
    videos = json.loads((DEMO / "demo_videos.json").read_text(encoding="utf-8"))
    out = []
    for shot, customer in customers.items():
        sha = hashlib.sha256((DEMO / shot).read_bytes()).hexdigest()
        cached = ClaimSet.model_validate_json((DEMO / f"{sha}.json").read_text(encoding="utf-8"))
        payee = next((c.fields.upi_id for c in cached.claims if c.type == "payee" and c.fields.upi_id), None)
        clip = videos.get(shot)
        out.append(
            {
                "id": shot.removesuffix(".png"),
                "customer_id": customer,
                "screenshot": f"/demo/files/{shot}",
                "video": f"/demo/files/{clip}" if clip and (DATA / "media" / clip).exists() else None,
                # the payee the ad asks the customer to pay, from the stored reader output; the amount is the customer's
                "payment_request": {"payee": payee, "source": "payee printed in the screenshot"} if payee else None,
            }
        )
    return out


@app.get("/demo/scenarios")
def demo_scenarios():
    return {"mock": True, "demo_mode": DEMO_MODE(), "scenarios": _scenarios()}


def DEMO_MODE() -> bool:  # noqa: N802
    return os.environ.get("KASAUTI_DEMO") == "1"


@app.get("/cases")
def api_cases(x_role: str = Header("customer")):
    reviewer_role(x_role)
    return reviewer.cases()


@app.get("/stats")
def api_stats(x_role: str = Header("customer")):
    return reviewer.stats(reviewer_role(x_role))


class DemoRun(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario: str


@app.post("/demo/run")
def demo_run(req: DemoRun):
    """Presenter button: the real pipeline on one demo artifact (read, video source check, records, rules, chain)."""
    if not DEMO_MODE():
        raise HTTPException(403, "demo runs need KASAUTI_DEMO=1")
    s = next((x for x in _scenarios() if x["id"] == req.scenario), None)
    if s is None:
        raise HTTPException(404, "no such demo scenario")
    claimset = reader.read((DEMO / f"{s['id']}.png").read_bytes())
    if s["video"]:
        from app.comparators import video

        clip = DATA / "media" / s["video"].removeprefix("/demo/files/")
        sha = hashlib.sha256(clip.read_bytes()).hexdigest()
        match = video.match(clip)
        footage_index.store(sha, match)
        quote = match.get("quote") or " ".join(match["transcript"].split()[:25])  # as the bank app does
        fields = {"person": "", "quote": quote, "media_sha256": sha}
        cs = claimset.model_dump(mode="json")
        cs["claims"].append({"id": f"c{len(cs['claims']) + 1}", "type": "endorsement", "fields": fields})
        claimset = ClaimSet.model_validate(cs)
    req2 = CheckRequest(claimset=claimset, customer_id=s["customer_id"], consent_id="consent-demo-run")
    return {"scenario": s["id"], "check_id": api_check(req2).check_id}


@app.post("/demo/reset")
def demo_reset_route():
    """Presenter Reset: evidence DB, dev key, MOCK registry additions, acks and events back to the seed."""
    if not DEMO_MODE():
        raise HTTPException(403, "demo reset needs KASAUTI_DEMO=1")
    from app import demo_reset

    demo_reset.reset()
    return demo_reset.counts()


@app.get("/demo/files/{name:path}")
def demo_file(name: str):
    allowed = {s["screenshot"] for s in _scenarios()} | {s["video"] for s in _scenarios() if s["video"]}
    if f"/demo/files/{name}" not in allowed:
        raise HTTPException(404, "not a demo artifact")
    return FileResponse(DEMO / name if name.endswith(".png") else DATA / "media" / name)


def _own_check(check_id: str, customer_id: str) -> None:
    """MOCK bank login: a customer reads only their own check (the customer id stands in for the session)."""
    rows = hashchain.checks("check_id = ?", (check_id,))
    if not rows or rows[0]["customer_id"] != customer_id:
        raise HTTPException(404, "no such check for this customer")


@app.get("/api/checks/{check_id}/records")
def api_check_records(check_id: str, customer_id: str):
    """The records each verdict was decided on, as the evidence chain stores them (source, fetched_at, mock, sha256)."""
    _own_check(check_id, customer_id)
    return [e["summary"] for e in hashchain.entries(check_id, "customer") if e["kind"] == "record"]


@app.get("/api/checks/{check_id}/pack")
def api_check_pack(check_id: str, customer_id: str):
    """The customer's own hashed evidence pack, as a file; X-Pack-SHA256 is the SHA-256 of exactly these bytes."""
    _own_check(check_id, customer_id)
    data = Path(pack.export(check_id, "customer")["json"]).read_bytes()
    headers = {"Content-Disposition": f'attachment; filename="pack-{check_id}.json"',
               "X-Pack-SHA256": hashlib.sha256(data).hexdigest()}  # fmt: skip
    return Response(data, media_type="application/json", headers=headers)
