from typing import Literal

from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict

from app import reader
from app.router.check import map_isins, run_check
from app.schemas.claims import ClaimSet
from app.schemas.verdict import CheckResult

app = FastAPI(title="Kasauti")
MAX_UPLOAD = 10 * 1024 * 1024


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
