"""Connectors, claim reader and the API on the demo-001 screenshot."""

import hashlib
import subprocess
import sys
import time

import pytest
from fastapi.testclient import TestClient

from app import reader
from app.connectors import aa_mock, isin_master, rbi, sebi, suspect_registry, upi
from app.main import app
from app.reader import offline
from app.router.check import run_check
from app.schemas.evidence import canonical
from tests.helpers import ROOT, renderable

DEMO = ROOT / "data" / "demo_cache" / "demo-001.png"
INJECTION = ROOT / "backend" / "tests" / "fixtures" / "fixture_injection.png"
DEMO_CUSTOMER = "SYN-C0001"  # synthetic fake_app_only case P0001
needs_tesseract = pytest.mark.skipif(not offline.os.path.exists(offline.TESSERACT), reason="Tesseract not installed")


def test_record_responses_hash_payload_and_label_mocks():
    recs = [
        *aa_mock.fetch(DEMO_CUSTOMER, "consent-mock-1"),
        isin_master.lookup("Infosys"),
        sebi.lookup("Zyphra Stock Club", None),
    ]
    recs += [rbi.lookup("Alpari"), upi.check("a.brk@validx"), suspect_registry.lookup("x@y")]
    for r in recs:
        assert r.sha256 == hashlib.sha256(canonical(r.payload).encode()).hexdigest()
        assert r.mock == (r.source.startswith("aa_mock") or r.source in {"upi", "suspect_registry"})


def test_aa_mock_asks_for_holdings_only():
    for r in aa_mock.fetch(DEMO_CUSTOMER, "consent-mock-1"):
        text = canonical(r.payload)
        assert "Transactions" not in text and "Profile" not in text and "pan" not in text
        assert r.consent_id == "consent-mock-1"


def test_isin_master_maps_demo_names():
    got = {
        n: isin_master.lookup(n).payload["isin"]
        for n in ("Reliance Industries", "Tata Consultancy Services", "Infosys")
    }
    assert got == {
        "Reliance Industries": "INE002A01018",
        "Tata Consultancy Services": "INE467B01029",
        "Infosys": "INE009A01021",
    }
    assert isin_master.lookup("Definitely Not A Listed Co").payload["isin"] is None


def test_cache_replays_stored_reader_output(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "cache")
    data = DEMO.read_bytes()
    cs = reader.read(data)
    assert cs.artifact_sha256 == hashlib.sha256(data).hexdigest()
    assert cs.reader.provider in {"offline", "bedrock", "anthropic"}
    with pytest.raises(LookupError):
        reader.read(b"not cached")


@needs_tesseract
def test_offline_reader_reads_demo(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "offline")
    cs = reader.read(DEMO.read_bytes())
    holdings = [c.fields for c in cs.claims if c.type == "holding"]
    assert [(h.instrument_name, h.quantity) for h in holdings] == [
        ("Reliance Industries", 5000),
        ("Tata Consultancy Services", 3000),
        ("Infosys", 8000),
    ]
    assert cs.portfolio_total_inr == 39800000
    assert any(c.type == "broker" and c.fields.name == "Zyphra Stock Club" for c in cs.claims)


@needs_tesseract
def test_text_in_image_never_changes_a_verdict(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "offline")
    cs = reader.read(INJECTION.read_bytes())
    assert "MATCHES" not in cs.model_dump_json()  # the instruction is not copied into any claim
    result, _ = run_check(cs, DEMO_CUSTOMER, "consent-mock-1")
    infosys = next(v for v in result.verdicts if v.claim_type == "holding")
    assert (infosys.outcome, infosys.reason_code) == ("CONTRADICTS", "HOLDING_NOT_FOUND_ALL_DEPOSITORIES")
    assert all(v.outcome != "MATCHES" for v in result.verdicts)


def test_api_read_then_check_demo(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "cache")
    client = TestClient(app)
    r = client.post("/api/read", files={"file": ("demo-001.png", DEMO.read_bytes(), "image/png")})
    assert r.status_code == 200, r.text
    claimset = r.json()
    t = time.perf_counter()
    r = client.post(
        "/api/check", json={"claimset": claimset, "customer_id": DEMO_CUSTOMER, "consent_id": "consent-mock-1"}
    )
    assert time.perf_counter() - t < 60
    assert r.status_code == 200, r.text
    body = r.json()
    total = body["summary"][0]
    assert total["reason_code"] == "HOLDINGS_TOTAL_NONE_FOUND"
    assert (total["params"]["found_count"], total["params"]["claimed_count"]) == (0, 3)
    broker = next(v for v in body["verdicts"] if v["claim_type"] == "broker")
    assert (broker["reason_code"], broker["params"]["name"]) == ("BROKER_NOT_ON_SEBI_LIST", "Zyphra Stock Club")
    result, _ = run_check(reader.read(DEMO.read_bytes()), DEMO_CUSTOMER, "consent-mock-1")
    for v in [*result.verdicts, *result.summary]:
        renderable(v)


def test_api_read_rejects_non_images():
    r = TestClient(app).post("/api/read", files={"file": ("x.txt", b"hello", "text/plain")})
    assert r.status_code == 415


def test_300_synthetic_portfolios_all_correct():
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "run_portfolios.py")], capture_output=True, text=True)
    assert out.returncode == 0 and "300/300 correct" in out.stdout, out.stdout
