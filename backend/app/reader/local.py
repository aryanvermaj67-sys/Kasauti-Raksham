"""Free local claim reader (LLM_PROVIDER=local): EasyOCR (hi+en) -> text -> Ollama on localhost -> ClaimSet.

The model only proposes claims, as JSON constrained to docs/formats/claims.schema.json (minus the fields code fills:
sha256, ids, reader). Nothing the model says reaches the router unless it validates as a ClaimSet; any failure ends in
ReaderError and the caller falls back to the offline reader. Text inside the image is data, never instructions.
Only loopback network calls are made (checked below).
"""

import json
import os
import re
import subprocess
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
MAX_TOKENS = 1500  # a runaway answer ends here (about 25 s on the GPU) instead of at the time limit
KEEP_ALIVE = os.environ.get(
    "KASAUTI_KEEP_ALIVE", "60m"
)  # Ollama unloads an idle model after 5 min; a cold load takes 100 s+
EXTRA_OPTIONS = json.loads(os.environ.get("KASAUTI_OLLAMA_OPTIONS", "{}"))  # e.g. {"num_gpu": 0} to measure on CPU
# defence in depth: a claim whose text reads like an instruction to us is dropped (verdicts come from rules anyway)
REG_NO = re.compile(r"IN[AHZ]\d{9}")  # same format the offline reader accepts
INSTRUCTION = re.compile(
    r"ignore (all |the |any )?(previous|prior|above|record)|disregard|mark (this|it)\b|say matches"
    r"|system prompt|पिछले (सभी )?निर्देश|अनदेखा|सत्यापित (कर|मान)|सुरक्षित (कर|मान)",
    re.I,
)
PROMPT = (Path(__file__).parent / "local_prompt.txt").read_text(encoding="utf-8")
DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
RUPEE_AS_RA = re.compile(r"(?<![\u0900-\u097F])र\s*(?=\d)")  # EasyOCR (hi+en) reads ₹ as र before a number
NUM = r"\d[\d,]*(?:\.\d+)?"
SCALE = {
    "crore": 1e7,
    "crores": 1e7,
    "cr": 1e7,
    "करोड़": 1e7,
    "lakh": 1e5,
    "lakhs": 1e5,
    "lac": 1e5,
    "l": 1e5,
    "लाख": 1e5,
}
AMOUNT = re.compile(rf"({NUM})\s*(crores?|cr\b|करोड़|lakhs?|lac\b|l\b|लाख)?", re.I)
QTY_WORDS = r"shares?|qty|quantity|units?|शेयर|मात्रा|यूनिट"
QTY = re.compile(rf"(?:{QTY_WORDS})(?:\s+held)?\s*[:ः\-]?\s*({NUM})|({NUM})\s*(?:{QTY_WORDS})", re.I)
RUPEES = re.compile(rf"(?:₹|rs\.?|inr)\s*({NUM})", re.I)
TOTAL_LINE = re.compile(r"\b(total|portfolio|account value)\b|कुल|पोर्टफोलियो", re.I)
UPI = re.compile(r"[\w.\-]+@[A-Za-z0-9.\-]+")


class ReaderError(Exception):
    """The local reader could not produce a valid ClaimSet; the caller falls back to the offline reader."""


@cache
def model_schema() -> dict:
    """What the model fills in, built from claims.schema.json: the field definitions of each claim type, laid out as a
    holdings list plus at most one broker, payee and platform (null when absent). A free list of claims let gemma loop
    on empty claims until the token limit. Code adds ids, sha256 and reader, and turns this into a claims list."""
    s = json.loads(SCHEMA.read_text(encoding="utf-8"))

    def fields(name):
        return s["$defs"][name]["properties"]["fields"]

    def maybe(name):
        return {"anyOf": [fields(name), {"type": "null"}]}

    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["language", "portfolio_total_inr", "holdings", "broker", "payee", "platform"],
        "properties": {
            "language": s["properties"]["language"],
            "portfolio_total_inr": s["properties"]["portfolio_total_inr"],
            "holdings": {"type": "array", "maxItems": 30, "items": fields("holding")},
            "broker": maybe("broker"),
            "payee": maybe("payee"),
            "platform": maybe("platform"),
        },
    }


def _as_claims(data: dict) -> list[dict]:
    """The model's layout (holdings list + single broker, payee, platform) as a claims list. A ready-made "claims"
    list is accepted too."""
    if "claims" in data:
        return data["claims"]
    one = [{"type": t, "fields": data[t]} for t in ("broker", "payee", "platform") if data.get(t)]
    return [{"type": "holding", "fields": h} for h in data["holdings"]] + one


@cache
def _easyocr():
    import bidi
    import bidi.algorithm

    # python-bidi 0.4.2 (pure Python; the 0.6 DLL can be blocked by Windows Application Control) lacks this name
    bidi.get_display = getattr(bidi, "get_display", bidi.algorithm.get_display)
    import easyocr
    import torch

    return easyocr.Reader(["hi", "en"], gpu=torch.cuda.is_available(), verbose=False)


IDENTIFIER = re.compile(
    r"[A-Za-z0-9_\-]+(?:\s*\.\s*[A-Za-z0-9_\-]+)*\s*@\s*[A-Za-z0-9.\-]+|(?<![A-Za-z0-9])IN[AHZ]\d{9}(?![A-Za-z0-9])"
)


def second_reading(image: bytes, text: str) -> str:
    """EasyOCR reads "@" as a letter and loses UPI handles. Tesseract reads them well, so any UPI handle or SEBI
    registration number it finds that the text lacks is appended on its own line. Without Tesseract: nothing added."""
    from app.reader import offline

    try:
        found = IDENTIFIER.findall(offline.ocr(image))
    except (OSError, subprocess.SubprocessError):
        return ""
    have = re.sub(r"\s+", "", text).casefold()
    lines = []
    for raw in dict.fromkeys(re.sub(r"\s+", "", f) for f in found):
        if raw.casefold() not in have:
            lines.append(f"SEBI Reg. No.: {raw}" if raw.startswith("IN") and "@" not in raw else f"UPI ID: {raw}")
    return "\n" + "\n".join(lines) if lines else ""


def ocr(image: bytes) -> str:
    text = clean_ocr("\n".join(_easyocr().readtext(image, detail=0)))
    return text + second_reading(image, text)


# OCR habits repaired below, each only where the printed format makes the right reading certain
REG_NO_MISREAD = re.compile(r"(?<![A-Za-z0-9])[|Il1!]N([AHZ])([0-9OIlSB]{9})(?![A-Za-z0-9])")  # SEBI reg no: |NZ0000..
SEBI_HANDLE = re.compile(
    r"([a-z0-9]+)\s*\.\s*(brk|mf)\s*[a@]\s*(valid[a-z0-9]+)", re.I
)  # name.brk@validbank, "@" read as a
LOOKALIKE_DIGITS = str.maketrans("OIlSB", "01158")
CAPITAL_O_IN_WORD = re.compile(r"(?<=[a-z])O(?=[a-z])")  # "ZerOdha": a capital O inside a lower-case word is a zero


def clean_ocr(text: str) -> str:
    """Undo EasyOCR habits: Devanagari digits for printed digits, rupee sign read as र, and look-alike glyphs in
    identifiers whose format fixes the reading (SEBI registration numbers, @valid handles, a zero inside a word)."""
    text = RUPEE_AS_RA.sub("₹ ", text.translate(DEVANAGARI_DIGITS))
    text = REG_NO_MISREAD.sub(lambda m: f"IN{m[1]}{m[2].translate(LOOKALIKE_DIGITS)}", text)
    text = SEBI_HANDLE.sub(lambda m: f"{m[1]}.{m[2].lower()}@{m[3]}", text)
    return CAPITAL_O_IN_WORD.sub("0", text)


def _num(s: str) -> float:
    return float(s.replace(",", ""))


def _amounts(text: str) -> list[float]:
    """Every number printed in the text (₹3.98 crore -> 39800000), once per appearance."""
    return [_num(n) * SCALE.get(unit.lower(), 1) if unit else _num(n) for n, unit in AMOUNT.findall(text)]


def _near(x, values) -> bool:
    return any(abs(x - v) <= 1 for v in values)


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
        "keep_alive": KEEP_ALIVE,
        "options": {"temperature": 0.2 if retry_note else 0, "num_predict": MAX_TOKENS, **EXTRA_OPTIONS},
        "messages": messages,
    }
    r = httpx.post(f"{OLLAMA}/api/chat", json=body, timeout=max(1.0, deadline - time.monotonic()))
    if r.status_code == 404:
        raise LookupError(model)
    r.raise_for_status()
    return r.json()["message"]["content"]


def _is_total_line(c: dict) -> bool:
    return c["fields"].get("quantity") is None and bool(TOTAL_LINE.search(c["fields"].get("instrument_name") or ""))


def _labelled_total(text: str, v: float) -> bool:
    """True if v is printed on a Total / Portfolio / कुल line (or the line after it)."""
    lines = text.splitlines()
    return any(TOTAL_LINE.search(ln) and _near(v, _amounts(" ".join(lines[i : i + 2]))) for i, ln in enumerate(lines))


def _check_numbers(claims: list[dict], total, text: str):
    """Numbers the OCR text does not back up become null: a model may move, copy or invent them."""
    printed = _amounts(text)
    qty_labelled = [_num(a or b) for a, b in QTY.findall(text)]
    rupee_labelled = [_num(n) for n in RUPEES.findall(text)]
    if total is not None and not _near(total, printed):
        total = None
    for c in [c for c in claims if c["type"] == "holding"]:
        f = c["fields"]
        if total is None and _is_total_line(c):
            total = f.get("value_inr")  # the model made a holding of the total line
        for k in ("quantity", "value_inr"):
            if f.get(k) is not None and not _near(f[k], printed):
                f[k] = None
        v = f.get("value_inr")
        if v is not None and _near(v, qty_labelled) and not _near(v, rupee_labelled):
            f["quantity"], f["value_inr"] = f.get("quantity") or v, None  # a number by a share label is a quantity
        q = f.get("quantity")
        if q is not None and _near(q, rupee_labelled) and not _near(q, qty_labelled):
            f["quantity"] = None  # a rupee amount is never a quantity
        v = f.get("value_inr")
        if (
            v is not None
            and total is not None
            and (len([c for c in claims if c["type"] == "holding"]) > 1 or _labelled_total(text, v))
            and abs(v - total) <= 1
            and sum(abs(v - p) <= 1 for p in printed) < 2
        ):
            f["value_inr"] = None  # printed once, as the total: copied from it, not that line's own value
    return [c for c in claims if c["type"] != "holding" or not _is_total_line(c)], total


NULLISH = {"null", "none", "n/a", "na", "nil", "-", ""}  # the model sometimes writes null as a word
NOT_A_FIRM = {"holdings", "portfolio", "total value", "home", "होल्डिंग्स", "पोर्टफोलियो", "कुल मूल्य", "होम"}


def _tidy(claims: list[dict]) -> list[dict]:
    """Words for null become null, and a claim that needs a name and has none (or only a page heading) is dropped."""
    out = []
    for c in claims:
        f = c["fields"]
        for k, v in f.items():
            if isinstance(v, str) and v.strip().lower() in NULLISH:
                f[k] = None
        name = f.get("instrument_name" if c["type"] == "holding" else "name")
        if c["type"] != "payee" and (not name or (c["type"] != "holding" and name.strip().lower() in NOT_A_FIRM)):
            continue
        out.append(c)
    return out


def _repair_rupee_digit(claims: list[dict], total):
    """A rupee sign read as the digit 2 puts a stray leading 2 on a value. If the printed total says which one (it is
    the only holding whose value, minus that 2, makes the lines add up to the total), take the 2 off."""
    held = [c["fields"] for c in claims if c["type"] == "holding"]
    values = [f.get("value_inr") for f in held]
    if total is None or not held or None in values or abs(sum(values) - total) <= 1:
        return
    fixes = [
        f
        for f in held
        if str(int(f["value_inr"])).startswith("2")
        and len(str(int(f["value_inr"]))) > 1
        and abs(sum(values) - f["value_inr"] + int(str(int(f["value_inr"]))[1:]) - total) <= 1
    ]
    if len(fixes) == 1:
        fixes[0]["value_inr"] = float(str(int(fixes[0]["value_inr"]))[1:])


REGISTERED_CUE = re.compile(
    r"(sebi|सेबी)[^\n]{0,30}(regist|licen|authori[sz]|पंजीकृत|रजिस्टर)|(regist|licen)[^\n]{0,30}(sebi|सेबी)|पंजीकृत|\bIN[AHZ]\d{9}\b",
    re.I,
)


def _ground(claims: list[dict], text: str) -> None:
    """The model may not claim more than the text says. A firm 'claims to be registered' only if the text says so, and
    an ISIN that the model put on several holdings stays only on the holding whose name comes last before it."""
    if not REGISTERED_CUE.search(text):
        for c in claims:
            if c["type"] == "broker":
                c["fields"]["claims_registered"] = False
    held = [c["fields"] for c in claims if c["type"] == "holding" and c["fields"].get("isin")]
    for isin in {f["isin"] for f in held if sum(g["isin"] == f["isin"] for g in held) > 1}:
        at = text.find(isin)
        owners = [f for f in held if f["isin"] == isin]
        before = [(text.rfind(f["instrument_name"], 0, max(at, 0)), f) for f in owners]
        keep = max(before, key=lambda p: p[0])[1] if at >= 0 and any(p[0] >= 0 for p in before) else None
        for f in owners:
            if f is not keep:
                f["isin"] = None


UPI_HANDLE = re.compile(r"[A-Za-z0-9_\-]+(?:\.[A-Za-z0-9_\-]+)*@[A-Za-z0-9.\-]+")
BROKER_WORD = re.compile(r"broker|ब्रोकर", re.I)
ADVISOR_WORD = re.compile(r"advis[eo]r|advisory|सलाहकार", re.I)


def _payee_from_text(claims: list[dict], text: str) -> None:
    """The model sometimes leaves payee null although a UPI handle is printed. A handle in the text (with its "@") is a
    payee claim; who it belongs to is read from the words around it, else "other"."""
    claims[:] = [  # a payee whose id was cleared (not a UPI id) names nothing: it does not count as read
        c
        for c in claims
        if c["type"] != "payee" or any(c["fields"].get(k) for k in ("upi_id", "account_no_last4", "ifsc"))
    ]
    if any(c["type"] == "payee" for c in claims):
        return
    handle = UPI_HANDLE.search(re.sub(r"\s*\.\s*", ".", text))
    if handle:
        who = "advisor" if ADVISOR_WORD.search(text) else "broker" if BROKER_WORD.search(text) else "other"
        fields = {"upi_id": handle[0], "account_no_last4": None, "ifsc": None, "described_as": who}
        claims.append({"type": "payee", "fields": fields})


def _printed_total(text: str):
    """The amount printed on (or just after) a Total / Portfolio / कुल line, if any."""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if TOTAL_LINE.search(ln):
            amounts = _amounts(" ".join(lines[i : i + 2]))
            if amounts:
                return amounts[0]
    return None


def _gap(cs: ClaimSet, printed) -> float | None:
    """How far the holdings' values are from the printed total; None when it cannot be told."""
    values = [c.fields.value_inr for c in cs.claims if c.type == "holding"]
    if printed is None or not values or None in values:
        return None
    return abs(sum(values) - printed)


def _complete(cs: ClaimSet, model: str, text: str, sha: str, deadline: float) -> ClaimSet:
    """If the holdings do not add up to the printed total, a line was probably missed: ask once more, saying so, and
    keep whichever answer is closer to the total."""
    printed = _printed_total(text)
    gap = _gap(cs, printed)
    if not gap or gap <= 1:
        return cs
    held = sum(c.fields.value_inr for c in cs.claims if c.type == "holding")
    note = (
        f"the holdings add up to {held:.0f} but the page total is {printed:.0f}; "
        "a holding line is missing or a number is wrong. List every holding line printed"
    )
    try:
        again = _to_claimset(_ask(model, text, note, deadline), sha, model, text)
    except (ValueError, KeyError, TypeError, AttributeError, IndexError, httpx.HTTPError):
        return cs
    new = _gap(again, printed)
    return again if new is not None and new < gap else cs


def _to_claimset(content: str, sha: str, model: str, text: str = "") -> ClaimSet:
    data = json.loads(content)
    claims = [
        c for c in _as_claims(data) if not INSTRUCTION.search(json.dumps(c.get("fields", {}), ensure_ascii=False))
    ]
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
        if c["type"] == "payee" and c["fields"].get("upi_id") and not UPI.fullmatch(c["fields"]["upi_id"]):
            c["fields"]["upi_id"] = (
                None  # OCR drops the dot in handles ("name desk@bank"); a guess could name another payee
            )
    claims = _tidy(claims)
    _payee_from_text(claims, text)
    _ground(claims, text)
    claims, total = _check_numbers(claims, data["portfolio_total_inr"], text)
    _repair_rupee_digit(claims, total)
    claims = [c for c in claims if c["type"] != "payee" or any(c["fields"].get(k) for k in payee_keys)]
    values = [c["fields"]["value_inr"] for c in claims if c["type"] == "holding"]
    if total is not None and values and None not in values and abs(total - sum(values)) > 1:
        total = None  # a total that disagrees with its own lines is a misread (the model once gave 10x the sum)
    return ClaimSet.model_validate(
        {
            "artifact_sha256": sha,
            "language": "hi" if re.search(r"[\u0900-\u097F]", text) else data["language"],  # from the text
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
                cs = _to_claimset(_ask(model, text, note, deadline), sha, model, text)
                return cs if note else _complete(cs, model, text, sha, deadline)
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
