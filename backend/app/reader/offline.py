"""Offline claim reader (FR-2.6): Tesseract OCR (eng+hin) plus regex field patterns -> ClaimSet.

Only these patterns can produce a claim, so any instruction written in the image is just unmatched text.
"""

import os
import re
import shutil
import subprocess
from datetime import datetime

from app.schemas.claims import ClaimSet
from app.schemas.evidence import IST

TESSERACT = (
    os.environ.get("TESSERACT_CMD") or shutil.which("tesseract") or r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)
MONEY = r"(?:Rs\.?|INR|₹)\s*(\d[\d,]*(?:\.\d+)?)"
HOLDING = re.compile(
    rf"^(?P<name>[A-Za-z][A-Za-z0-9&.' -]*?)\s+(?P<qty>\d[\d,]*)\s*(?:shares|qty|units)?\s+{MONEY}\s*$", re.I | re.M
)
TOTAL = re.compile(rf"(?:portfolio|total|current)\s+value\s*[:\-]?\s*{MONEY}", re.I)
UPI = re.compile(r"[A-Za-z0-9][\w.\-]*@[A-Za-z][A-Za-z0-9]+")
REG_NO = re.compile(r"\bIN[AHZ]\d{9}\b")
SEBI_REGISTERED = re.compile(r"SEBI\s+regist", re.I)
BROKER_LABEL = re.compile(r"^\s*broker\s*[:\-]\s*(.+)$", re.I | re.M)


def ocr(image: bytes) -> str:
    if not os.path.exists(TESSERACT):
        raise FileNotFoundError(f"Tesseract not found at {TESSERACT}; set TESSERACT_CMD")
    args = [TESSERACT, "stdin", "stdout", "-l", "eng+hin", "--psm", "6"]
    return subprocess.run(args, input=image, capture_output=True, check=True, timeout=120).stdout.decode("utf-8")


def num(s):
    return float(s.replace(",", ""))


def parse(text: str, sha: str) -> ClaimSet:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    claims = []
    for m in HOLDING.finditer(text):
        fields = {
            "instrument_name": m["name"].strip(),
            "isin": None,
            "quantity": int(num(m["qty"])),
            "value_inr": num(m[3]),
        }
        claims.append({"type": "holding", "fields": fields})
    registered = any(SEBI_REGISTERED.search(ln) for ln in lines)
    label = BROKER_LABEL.search(text)
    # shortcut: without a "Broker:" label, the app's name is taken as the line above "SEBI Registered"
    name = (
        label[1].strip()
        if label
        else next((lines[i - 1] for i, ln in enumerate(lines) if i and SEBI_REGISTERED.search(ln)), None)
    )
    if name:
        reg = REG_NO.search(text)
        claims.append(
            {
                "type": "broker",
                "fields": {"name": name, "sebi_reg_no": reg[0] if reg else None, "claims_registered": registered},
            }
        )
    upi = UPI.search(text)
    if upi:
        # money asked for by the app that names a broker is described as going to that broker
        payee = {
            "upi_id": upi[0],
            "account_no_last4": None,
            "ifsc": None,
            "described_as": "broker" if name else "other",
        }
        claims.append({"type": "payee", "fields": payee})
    total = TOTAL.search(text)
    devanagari = len(re.findall(r"[\u0900-\u097F]", text))
    return ClaimSet.model_validate(
        {
            "artifact_sha256": sha,
            "language": "hi" if devanagari > len(re.findall(r"[A-Za-z]", text)) else "en",
            "claims": [{"id": f"c{i}", **c} for i, c in enumerate(claims, 1)],
            "portfolio_total_inr": num(total[1]) if total else None,
            "reader": {"provider": "offline", "produced_at": datetime.now(IST)},
        }
    )


def read(image: bytes, sha: str) -> ClaimSet:
    return parse(ocr(image), sha)
