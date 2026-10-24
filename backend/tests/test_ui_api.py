"""Endpoints the customer app uses: demo scenarios and files, consent refusal, own records, own evidence pack."""

import hashlib

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from app import main
from tests.helpers import ROOT

DEMO = ROOT / "data" / "demo_cache" / "demo-001.png"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("EVIDENCE_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("LLM_PROVIDER", "cache")
    return TestClient(main.app)


def check(client, scope=("CDSL", "NSDL"), customer="SYN-C0001"):
    claimset = client.post("/api/read", files={"file": ("d.png", DEMO.read_bytes(), "image/png")}).json()
    body = {"claimset": claimset, "customer_id": customer, "consent_id": "consent-mock-1", "consent_scope": list(scope)}
    return client.post("/api/check", json=body).json()


def test_scenarios_list_the_demo_artifacts_and_serve_only_them(client):
    s = client.get("/demo/scenarios").json()
    print("\n", s)
    assert s["mock"] and [x["id"] for x in s["scenarios"]] == ["demo-001", "demo-002", "demo-003"]
    first = s["scenarios"][0]
    assert client.get(first["screenshot"]).content == DEMO.read_bytes()
    for bad in ("demo_customers.json", "../../.env", "fakes/../../../.env", "demo-004.png"):
        assert client.get(f"/demo/files/{bad}").status_code == 404


def test_refused_consent_checks_registries_only_and_never_contradicts_a_holding(client):
    r = check(client, scope=())
    holdings = [(v["outcome"], v["reason_code"]) for v in r["verdicts"] if v["claim_type"] == "holding"]
    others = {v["claim_type"]: v["outcome"] for v in r["verdicts"] if v["claim_type"] != "holding"}
    print(f"\nrefused: holdings {holdings}, others {others}, summary {r['summary']}")
    assert holdings and all(h == ("NO_RECORD", "HOLDING_NO_CONSENT") for h in holdings)
    assert r["summary"] == [] and others["broker"] == "CONTRADICTS"  # the SEBI list is still checked


def test_records_and_pack_only_for_the_customer_who_ran_the_check(client):
    cid = check(client)["check_id"]
    recs = client.get(f"/api/checks/{cid}/records", params={"customer_id": "SYN-C0001"}).json()
    assert {"source", "fetched_at", "mock", "sha256"} <= set(recs[0]) and any(r["mock"] for r in recs)
    assert client.get(f"/api/checks/{cid}/records", params={"customer_id": "SYN-C0002"}).status_code == 404
    p = client.get(f"/api/checks/{cid}/pack", params={"customer_id": "SYN-C0001"})
    print(f"\npack {len(p.content)} bytes, X-Pack-SHA256 {p.headers['x-pack-sha256']}")
    assert p.headers["x-pack-sha256"] == hashlib.sha256(p.content).hexdigest()
    assert p.json()["chain_valid"] is True
    assert client.get(f"/api/checks/{cid}/pack", params={"customer_id": "SYN-C0002"}).status_code == 404
