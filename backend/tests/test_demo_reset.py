"""Full demo flow (check, events, video record, approval, ack), then reset: registry and reviewer queue back to seed."""

from fastapi.testclient import TestClient

from app import demo_reset, main, trigger
from app.connectors import footage_index, suspect_registry
from app.evidence import hashchain
from tests.helpers import ROOT

DEMO = ROOT / "data" / "demo_cache" / "demo-001.png"
PAYEE = "zyphrastock.invest@mockupi"
REVIEWER = {"X-Role": "reviewer"}


def test_full_flow_then_reset_restores_seed(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "cache")
    monkeypatch.delenv("EVIDENCE_KEY", raising=False)  # dev key file path, which reset must also clear
    seed = demo_reset.counts()
    client = TestClient(main.app)
    claimset = client.post("/api/read", files={"file": ("d.png", DEMO.read_bytes(), "image/png")}).json()
    body = {"claimset": claimset, "customer_id": "SYN-C0001", "consent_id": "consent-mock-1"}
    check_id = client.post("/api/check", json=body).json()["check_id"]
    client.post("/api/events", json={"kind": "bank_callback", "check_id": check_id, "customer_id": "SYN-C0001"})
    footage_index.store("ab" * 32, {"source": None})
    assert [c["check_id"] for c in client.get("/api/reviewer/queue", headers=REVIEWER).json()] == [check_id]
    client.post(f"/api/reviewer/checks/{check_id}/approve", json={"reason": "test"}, headers=REVIEWER)
    client.post(f"/api/reviewer/checks/{check_id}/pack", headers=REVIEWER)
    other = trigger.for_customer("SYN-C0011")[0]["campaign"]
    client.post("/api/trigger/SYN-C0011/ack", json={"campaign": other})
    used = demo_reset.counts()
    print(f"\nseed {seed}\nafter flow {used}")
    assert used["registry additions (mock)"] == 1 and used["events logged"] == 1 and used["trigger acks"] == 1
    assert suspect_registry.lookup(PAYEE).payload["hit"]

    demo_reset.reset()
    after = demo_reset.counts()
    print(f"after reset {after}")
    assert after == seed
    assert after["evidence checks"] == after["reviewer queue"] == after["registry additions (mock)"] == 0
    assert after["dev key file"] == 0 and not hashchain.DB.exists()
    assert suspect_registry.lookup(PAYEE).payload["hit"] is None
    assert client.get("/api/reviewer/queue", headers=REVIEWER).json() == []
    assert not footage_index.RESULTS.exists()
