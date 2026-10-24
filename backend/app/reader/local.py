"""Free local claim reader (LLM_PROVIDER=local): EasyOCR (hi+en) -> text -> Ollama on localhost -> ClaimSet.

The model only proposes claims, as JSON constrained to docs/formats/claims.schema.json (minus the fields code fills:
sha256, ids, reader). Nothing the model says reaches the router unless it validates as a ClaimSet; any failure ends in
ReaderError and the caller falls back to the offline reader. Text inside the image is data, never instructions.
Only loopback network calls are made (checked below).
"""

import json
import os
import re
import time
from datetime import datetime
from functools import cache
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.connectors import DATA
from app.schemas.claims import ClaimSet
from app.schemas.evidence import IST

SCHEMA = DATA.parent / "docs" / "formats" / "claims.schema.json"
OLLAMA = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
MODELS = [
    os.environ.get("KASAUTI_LOCAL_MODEL", "gemma3:4b"),
    "qwen2.5:3b",
]  # default (scored best in docs/LOCAL_READER_EVAL_GPU.md), fallback
TIMEOUT_S = 60
EXTRA_OPTIONS = json.loads(os.environ.get("KASAUTI_OLLAMA_OPTIONS", "{}"))  # e.g. {"num_gpu": 0} to measure on CPU
# defence in depth: a claim whose text reads like an instruction to us is dropped (verdicts come from rules anyway)
REG_NO = re.compile(r"IN[AHZ]\d{9}")  # same format the offline reader accepts
INSTRUCTION = re.compile(
    r"ignore (all |the |any )?(previous|prior|above|record)|disregard|mark (this|it)\b|say matches"
    r"|system prompt|पिछले (सभी )?निर्देश|अनदेखा|सत्यापित (कर|मान)|सुरक्षित (कर|मान)",
    re.I,
)
PROMPT = (Path(__file__).parent / "local_prompt.txt").read_text(encoding="utf-8")


class ReaderError(Exception):
    """The local reader could not produce a valid ClaimSet; the caller falls back to the offline reader."""


@cache
def model_schema() -> dict:
    """claims.schema.json as the model sees it: no sha256/reader/ids (code fills them), no endorsement (video only)."""
    s = json.loads(SCHEMA.read_text(encoding="utf-8"))
    defs = s["$defs"]
    for name in ("holding", "broker", "payee", "platform"):
        defs[name]["properties"].pop("id")
        defs[name]["required"].remove("id")
    defs["claim"] = {"oneOf": [{"$ref": f"#/$defs/{n}"} for n in ("holding", "broker", "payee", "platform")]}
    for k in ("artifact_sha256", "reader"):
        s["properties"].pop(k)
        s["required"].remove(k)
    return s


@cache
def _easyocr():
    import bidi
    import bidi.algorithm

    # python-bidi 0.4.2 (pure Python; the 0.6 DLL can be blocked by Windows Application Control) lacks this name
    bidi.get_display = getattr(bidi, "get_display", bidi.algorithm.get_display)
    import easyocr
    import torch

    return easyocr.Reader(["hi", "en"], gpu=torch.cuda.is_available(), verbose=False)


def ocr(image: bytes) -> str:
    return "\n".join(_easyocr().readtext(image, detail=0))


def _check_loopback() -> None:
    if (urlparse(OLLAMA).hostname or "") not in {"127.0.0.1", "localhost", "::1"}:
        raise ReaderError(f"OLLAMA_HOST={OLLAMA} is not loopback; the local reader makes localhost calls only")


def _ask(model: str, text: str, retry_note: str | None, deadline: float) -> str:
    messages = [{"role": "user", "content": PROMPT + text}]
    if retry_note:
        note = f"Your previous answer was invalid ({retry_note}). Answer again with only valid JSON."
        messages.append({"role": "user", "content": note})
    body = {
        "model": model,
        "stream": False,
        "format": model_schema(),
        "options": {"temperature": 0.2 if retry_note else 0, **EXTRA_OPTIONS},
        "messages": messages,
    }
    r = httpx.post(f"{OLLAMA}/api/chat", json=body, timeout=max(1.0, deadline - time.monotonic()))
    if r.status_code == 404:
        raise LookupError(model)
    r.raise_for_status()
    return r.json()["message"]["content"]


def _to_claimset(content: str, sha: str, model: str) -> ClaimSet:
    data = json.loads(content)
    claims = [c for c in data["claims"] if not INSTRUCTION.search(json.dumps(c.get("fields", {}), ensure_ascii=False))]
    order = (
        "holding",
        "broker",
        "payee",
        "platform",
    )  # the offline reader's order, so the result screen reads the same
    claims.sort(key=lambda c: order.index(c["type"]))
    payee_keys = ("upi_id", "account_no_last4", "ifsc")  # a payee that names nothing is not a claim
    claims = [c for c in claims if c["type"] != "payee" or any(c["fields"].get(k) for k in payee_keys)]
    for c in claims:
        # a registration number is only ever in SEBI's format; the model once returned "SEBI Registered Broker"
        if c["type"] == "broker" and not REG_NO.fullmatch(str(c["fields"].get("sebi_reg_no"))):
            c["fields"]["sebi_reg_no"] = None
    values = [c["fields"]["value_inr"] for c in claims if c["type"] == "holding"]
    total = data["portfolio_total_inr"]
    if total is not None and values and None not in values and abs(total - sum(values)) > 1:
        total = None  # a total that disagrees with its own lines is a misread (the model once gave 10x the sum)
    return ClaimSet.model_validate(
        {
            "artifact_sha256": sha,
            "language": data["language"],
            "claims": [{"id": f"c{i}", **c} for i, c in enumerate(claims, 1)],
            "portfolio_total_inr": total,
            "reader": {"provider": "local", "produced_at": datetime.now(IST), "model": model},
        }
    )


def read_text(text: str, sha: str) -> ClaimSet:
    """OCR text -> validated ClaimSet. One retry on invalid output; a missing model moves on to the next one."""
    _check_loopback()
    deadline = time.monotonic() + TIMEOUT_S
    for model in dict.fromkeys(MODELS):
        note = None
        for _attempt in range(2):
            try:
                return _to_claimset(_ask(model, text, note, deadline), sha, model)
            except LookupError:
                break  # model not pulled: try the fallback model
            except (
                ValueError,
                KeyError,
                TypeError,
                AttributeError,
                IndexError,
            ) as e:  # bad JSON or a shape the schema forbids
                note = str(e).splitlines()[0][:200]
            except httpx.HTTPError as e:  # Ollama down, timeout, 5xx
                raise ReaderError(f"Ollama call failed: {type(e).__name__}: {e}") from e
        else:
            raise ReaderError(f"{model} gave invalid output twice: {note}")
    raise ReaderError(f"none of the models {MODELS} is pulled in Ollama")


def read(image: bytes, sha: str) -> ClaimSet:
    return read_text(ocr(image), sha)


def warm_up() -> None:
    """Load the model and compile its JSON grammar once (the first call took 147 s cold, over the 60 s limit)."""
    try:
        _easyocr()
        read_text("Warm up 1 share Rs. 1", "0" * 64)
    except Exception as e:  # never block startup; the first real call may then fall back to offline
        print(f"local reader warm-up failed: {e}", flush=True)
