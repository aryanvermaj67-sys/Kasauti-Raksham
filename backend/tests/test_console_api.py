"""Reviewer console and presenter endpoints: cases by state, computed stats, MOCK network, demo run and reset gates."""

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from app import main
from app.evidence import hashchain
from tests.helpers import ROOT

DEMO = ROOT / "data" / "demo_cache"
R = {"X-Role": "reviewer"}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("EVIDENCE_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("LLM_PROVIDER", "cache")
    return TestClient(main.app)


def check(client, shot, customer):
    claimset = client.post("/api/read", files={"file": ("d.png", (DEMO / shot).read_bytes(), "image/png")}).json()
    body = {"claimset": claimset, "customer_id": customer, "consent_id": "consent-mock-1"}
    return client.post("/api/check", json=body).json()["check_id"]


def test_cases_move_from_new_to_in_review_to_approved(client):
    a, b = check(client, "demo-001.png", "SYN-C0001"), check(client, "demo-002.png", "SYN-C0028")
    assert client.get("/cases").status_code == 403  # customer role
    states = lambda: {k: [c["check_id"] for c in v] for k, v in client.get("/cases", headers=R).json().items()}  # noqa: E731
    assert states() == {"new": [a], "in_review": [], "approved": [], "rejected": []}  # demo-002 matches: no case
    client.get(f"/api/reviewer/checks/{a}", headers=R)
    assert states()["in_review"] == [a]
    client.post(f"/api/reviewer/checks/{a}/approve", json={"reason": "x"}, headers=R)
    print("\n", states())
    assert states()["approved"] == [a] and b not in sum(states().values(), [])
    kinds = [e["kind"] for e in hashchain.entries(a, "reviewer")]
    assert kinds[-1] == "review" and hashchain.verify_chain(a)[0]  # the decision is in the chain, chain intact


def test_stats_are_computed_from_the_evidence_store(client):
    empty = client.get("/stats", headers=R).json()
    assert empty["checks"] == 0 and empty["median_latency_s"] is None
    ids = [check(client, "demo-001.png", "SYN-C0001"), check(client, "demo-002.png", "SYN-C0028")]
    s = client.get("/stats", headers=R).json()
    print("\n", s)
    assert s["checks"] == 2 and s["latency_samples"] == 2 and s["median_latency_s"] >= 0
    seen = {"MATCHES": 0, "CONTRADICTS": 0, "NO_RECORD": 0}  # what the two checks actually returned
    for cid in ids:
        for v in client.get(f"/api/reviewer/checks/{cid}", headers=R).json()["result"]["verdicts"]:
            seen[v["outcome"]] += 1
    assert s["outcomes"] == seen
    assert s["prompt_rate"] == {"prompts": 40, "customers": 300, "per_1000": 133}


def test_detail_network_panel_comes_from_mock_registry_and_ledger(client):
    a = check(client, "demo-001.png", "SYN-C0001")
    net = client.get(f"/api/reviewer/checks/{a}", headers=R).json()["network"]
    print("\n", net)
    assert [n["payee"] for n in net] == ["zyphrastock.invest@mockupi"]
    assert net[0]["registry_hit"] is None and net[0]["ledger_payers"]  # payers come from the synthetic ledger


def test_demo_run_and_reset_need_demo_mode(client, monkeypatch):
    monkeypatch.delenv("KASAUTI_DEMO", raising=False)
    assert client.post("/demo/reset").status_code == 403
    assert client.post("/demo/run", json={"scenario": "demo-002"}).status_code == 403
    assert client.get("/demo/scenarios").json()["demo_mode"] is False
    monkeypatch.setenv("KASAUTI_DEMO", "1")
    run = client.post("/demo/run", json={"scenario": "demo-002"}).json()
    assert run["check_id"].startswith("chk-") and len(hashchain.checks()) == 1
    after = client.post("/demo/reset").json()
    print("\n", run, after)
    assert after["evidence checks"] == 0 and hashchain.checks() == []
