"""Evidence chain (FR-9), reviewer console (FR-10) and complaint text, on the demo-001 check."""

import json
import re
import sqlite3
from datetime import datetime, timedelta

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from app import main, trigger
from app.connectors import suspect_registry
from app.evidence import hashchain, pack
from app.evidence.hashchain import _minimal
from app.schemas.evidence import IST, make_record
from tests.helpers import ROOT, TEMPLATES

DEMO = ROOT / "data" / "demo_cache" / "demo-001.png"
PAYEE = "zyphrastock.invest@mockupi"
REVIEWER = {"X-Role": "reviewer"}


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("EVIDENCE_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("LLM_PROVIDER", "cache")
    monkeypatch.setattr(hashchain, "DB", tmp_path / "kasauti.db")
    monkeypatch.setattr(pack, "PACKS", tmp_path / "packs")
    monkeypatch.setattr(suspect_registry, "ADDITIONS", tmp_path / "additions.json")
    monkeypatch.setattr(trigger, "ACKS", tmp_path / "acks.json")


def customer_check(client):
    claimset = client.post("/api/read", files={"file": ("d.png", DEMO.read_bytes(), "image/png")}).json()
    body = {"claimset": claimset, "customer_id": "SYN-C0001", "consent_id": "consent-mock-1"}
    return client.post("/api/check", json=body).json()["check_id"]


def test_untouched_chain_verifies_and_one_changed_byte_breaks_it():
    client = TestClient(main.app)
    a, b = customer_check(client), customer_check(client)
    ok, why = hashchain.verify_chain(a)
    print(f"\nuntouched chain {a}: {ok} ({why})")
    assert ok
    with sqlite3.connect(hashchain.DB) as con:  # flip one byte of one stored ciphertext
        blob = bytearray(con.execute("SELECT blob FROM entries WHERE check_id=? AND seq=2", (a,)).fetchone()[0])
        blob[40] ^= 1
        con.execute("UPDATE entries SET blob=? WHERE check_id=? AND seq=2", (bytes(blob), a))
        h = con.execute("SELECT content_sha256 FROM entries WHERE check_id=? AND seq=1", (b,)).fetchone()[0]
        con.execute(
            "UPDATE entries SET content_sha256=? WHERE check_id=? AND seq=1", (("0" if h[0] != "0" else "1") + h[1:], b)
        )
    for cid in (a, b):
        ok, why = hashchain.verify_chain(cid)
        print(f"after changing one stored byte, chain {cid}: {ok} ({why})")
        assert not ok


def test_holdings_kept_minimal_and_everything_encrypted_at_rest():
    cid = customer_check(TestClient(main.app))
    records = [e["summary"] for e in hashchain.entries(cid, "reviewer") if e["kind"] == "record"]
    aa = [r for r in records if r["source"].startswith("aa_mock")]
    assert len(aa) == 2 and all(set(r["isins_claimed"]) == {"INE002A01018", "INE467B01029", "INE009A01021"} for r in aa)
    assert all(r["isins_found"] == [] and "payload" not in r for r in aa)
    raw = hashchain.DB.read_bytes()
    assert b"INE002A01018" not in raw and b"Zyphra" not in raw and b"Reliance" not in raw


def test_video_record_keeps_source_offset_ranges_and_file_hash():
    payload = {
        "source_found": True,
        "source_clip": "dev_01.mp4",
        "similarity": 0.998,
        "offset_s": 5,
        "transcript_same": False,
        "changed_ranges": ["0:11-0:13"],
        "transcript": "long text",
        "quote": "x",
    }
    rec = make_record("footage_index", payload, mock=True)
    kept = _minimal(rec, [], ["ab" * 32])
    assert kept["source_clip"] == "dev_01.mp4" and kept["offset_s"] == 5 and kept["changed_ranges"] == ["0:11-0:13"]
    assert kept["media_sha256"] == ["ab" * 32] and kept["sha256"] == rec.sha256 and "transcript" not in kept


def test_reads_are_logged_with_role_and_customers_cannot_read_reviewer_data():
    client = TestClient(main.app)
    cid = customer_check(client)
    for url in ("/api/reviewer/queue", f"/api/reviewer/checks/{cid}"):
        assert client.get(url).status_code == 403
        assert client.get(url, headers={"X-Role": "customer"}).status_code == 403
    assert (
        client.post(f"/api/reviewer/checks/{cid}/approve", json={}, headers={"X-Role": "customer"}).status_code == 403
    )
    assert client.get(f"/api/reviewer/checks/{cid}", headers=REVIEWER).json()["chain"]["valid"] is True
    with sqlite3.connect(hashchain.DB) as con:
        assert ("reviewer", cid) in con.execute("SELECT role, check_id FROM read_log").fetchall()


def test_one_report_never_lists_an_account_without_approval():
    client = TestClient(main.app)
    cid = customer_check(client)
    assert client.get("/api/registry/lookup", params={"identifier": PAYEE}).json()["payload"]["hit"] is None
    assert [q["check_id"] for q in client.get("/api/reviewer/queue", headers=REVIEWER).json()] == [cid]
    out = client.post(
        f"/api/reviewer/checks/{cid}/approve", json={"reason": "app and record disagree"}, headers=REVIEWER
    ).json()
    ledger = json.loads((ROOT / "data" / "synthetic" / "ledger.json").read_text(encoding="utf-8"))
    assert out["other_customers_who_paid"] == ledger["demo_payee_customers"]
    assert client.get("/api/registry/lookup", params={"identifier": PAYEE}).json()["payload"]["hit"]["check_id"] == cid
    assert client.get("/api/reviewer/queue", headers=REVIEWER).json() == []
    assert hashchain.verify_chain(cid)[0]  # the review decision is chained too


def test_reject_needs_a_reason_and_is_logged():
    client = TestClient(main.app)
    cid = customer_check(client)
    assert client.post(f"/api/reviewer/checks/{cid}/reject", json={"reason": " "}, headers=REVIEWER).status_code == 422
    r = client.post(f"/api/reviewer/checks/{cid}/reject", json={"reason": "customer's own broker"}, headers=REVIEWER)
    assert r.json()["status"] == "rejected"
    review = [e for e in hashchain.entries(cid, "reviewer") if e["kind"] == "review"][0]["summary"]
    assert review == {"decision": "rejected", "role": "reviewer", "reason": "customer's own broker"}
    assert client.get("/api/registry/lookup", params={"identifier": PAYEE}).json()["payload"]["hit"] is None


def test_retention_purges_expired_evidence():
    cid = customer_check(TestClient(main.app))
    assert hashchain.purge_expired(datetime.now(IST) + timedelta(days=29)) == 0
    assert hashchain.purge_expired(datetime.now(IST) + timedelta(days=31)) == 1
    assert hashchain.checks("check_id = ?", (cid,)) == [] and hashchain.verify_chain(cid) == (False, "no entries")


def test_pack_export_is_a_hash_listing_not_a_certificate():
    client = TestClient(main.app)
    cid = customer_check(client)
    out = client.post(f"/api/reviewer/checks/{cid}/pack", headers=REVIEWER).json()
    schema = json.loads((ROOT / "docs" / "formats" / "evidence_pack.schema.json").read_text(encoding="utf-8"))
    data = json.loads(open(out["json"], encoding="utf-8").read())
    assert not list(Draft202012Validator(schema).iter_errors(data)) and data["chain_valid"] is True
    page = open(out["html"], encoding="utf-8").read()
    assert "Hash listing to support a certificate" in page and "not a legal certificate" in page
    assert all(e["entry_hash"] in page for e in data["entries"])


def test_complaint_names_the_video_finding_and_pack_in_both_languages():
    params = {"source_clip": "dev_01.mp4", "time_ranges": "0:11-0:13", "pack_id": "pack-chk-1"}
    for lang in TEMPLATES:
        ui = json.loads((ROOT / "backend" / "app" / "templates" / f"messages_{lang}.json").read_text(encoding="utf-8"))[
            "ui"
        ]
        text = " ".join(
            re.sub(r"\{(\w+)\}", lambda m: params[m[1]], ui[k]) for k in ("complaint_video", "complaint_pack")
        )
        print(f"\n[{lang}] {text}")
        assert all(v in text for v in params.values())
