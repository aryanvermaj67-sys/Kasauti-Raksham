"""Endpoints the bank app needs: ISIN candidates for ambiguous names, and the events log."""

import json

from fastapi.testclient import TestClient

from app import main
from app.router.check import run_check
from app.schemas.claims import ClaimSet
from tests.helpers import render

ETF_STYLE = "Aditya Birla Sun Life Mutual Fund"  # BSE issuer name shared by many ETFs


def test_candidates_list_every_isin_for_an_etf_style_name():
    body = TestClient(main.app).get("/api/isin/candidates", params={"name": ETF_STYLE}).json()
    isins = [c["isin"] for c in body["candidates"]]
    assert len(isins) > 1 and len(set(isins)) == len(isins) and all(i.startswith("INF") for i in isins)
    one = TestClient(main.app).get("/api/isin/candidates", params={"name": "Infosys"}).json()["candidates"]
    assert [c["isin"] for c in one] == ["INE009A01021"]


def test_skipped_choice_gives_holding_name_ambiguous():
    claimset = ClaimSet.model_validate(
        {
            "artifact_sha256": "0" * 64,
            "language": "en",
            "portfolio_total_inr": None,
            "reader": {"provider": "offline", "produced_at": "2026-10-24T10:00:00+05:30"},
            "claims": [
                {
                    "id": "c1",
                    "type": "holding",
                    "fields": {"instrument_name": ETF_STYLE, "isin": None, "quantity": 10, "value_inr": None},
                }
            ],
        }
    )
    v = run_check(claimset, "SYN-C0001", "consent-mock-1")[0].verdicts[0]
    assert (v.outcome, v.reason_code) == ("NO_RECORD", "HOLDING_NAME_AMBIGUOUS")
    assert v.params["candidate_count"] > 1
    for lang in ("en", "hi"):
        assert str(v.params["candidate_count"]) in render(v, lang)["record"]


def test_events_are_logged(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "EVENTS", tmp_path / "events.jsonl")
    client = TestClient(main.app)
    for kind in ("trusted_contact", "bank_callback", "still_pay"):
        r = client.post("/api/events", json={"kind": kind, "check_id": "chk-1", "customer_id": "SYN-C0001"})
        assert r.status_code == 200 and r.json()["mock"] == (kind != "still_pay")
    rows = [json.loads(line) for line in (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["kind"] for r in rows] == ["trusted_contact", "bank_callback", "still_pay"]
    bad = client.post("/api/events", json={"kind": "auto_submit_1930", "check_id": "chk-1", "customer_id": "x"})
    assert bad.status_code == 422
