"""Video source check end to end through the API, with the network disabled. Dev clips and their own index
(data/footage_index_dev), not the consented set or its index."""

import json
import re
import socket

import pytest
from fastapi.testclient import TestClient

from app import main
from app.comparators import video
from app.connectors import footage_index
from tests.helpers import ROOT, TEMPLATES, render

MEDIA = ROOT / "data" / "media"
DEV_INDEX = ROOT / "data" / "footage_index_dev"
pytestmark = pytest.mark.skipif(
    not (ROOT / "models" / "whisper").exists()
    or not (DEV_INDEX / "clips.json").exists()
    or not (MEDIA / "fakes").exists(),
    reason="video models, dev footage index or dev clips not on this machine (all git-ignored)",
)


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    connect = socket.socket.connect

    def guard(self, address):
        host = address[0] if isinstance(address, tuple) else address
        if host not in ("127.0.0.1", "::1", "localhost"):
            raise OSError(f"network disabled in this test: {address}")
        return connect(self, address)

    monkeypatch.setattr(socket.socket, "connect", guard)
    monkeypatch.setattr(footage_index, "RESULTS", tmp_path / "video")
    monkeypatch.setattr(video, "INDEX", DEV_INDEX)
    video._index.cache_clear()
    yield
    video._index.cache_clear()


def upload_and_check(clip):
    client = TestClient(main.app)
    r = client.post("/api/video", files={"file": (clip.name, clip.read_bytes(), "video/mp4")})
    assert r.status_code == 200, r.text
    body = r.json()
    fields = {
        "person": "DEV clip speaker",
        "quote": body["match"].get("quote") or "",
        "media_sha256": body["media_sha256"],
    }
    claimset = {
        "artifact_sha256": body["media_sha256"],
        "language": "en",
        "portfolio_total_inr": None,
        "reader": {"provider": "offline", "produced_at": "2026-10-24T10:00:00+05:30"},
        "claims": [{"id": "v1", "type": "endorsement", "fields": fields}],
    }
    r = client.post(
        "/api/check", json={"claimset": claimset, "customer_id": "SYN-C0001", "consent_id": "consent-mock-1"}
    )
    assert r.status_code == 200, r.text
    return body, r.json()["verdicts"][0]


def test_fake_clip_contradicts_with_changed_time_range():
    body, v = upload_and_check(MEDIA / "fakes" / "dev_01_fake_crf32.mp4")
    assert body["record"]["source"] == "footage_index" and body["record"]["mock"] is True
    assert body["match"]["source_clip"] == "dev_01.mp4" and body["match"]["offset_s"] == 5
    assert (v["outcome"], v["reason_code"]) == ("CONTRADICTS", "ENDORSEMENT_WORDS_CHANGED")
    assert all(re.fullmatch(r"\d+:\d\d-\d+:\d\d", t) for t in v["params"]["time_ranges"])
    assert body["match"]["timings_s"]["source_search"] < 5


def test_reencoded_original_matches():
    _, v = upload_and_check(MEDIA / "fakes" / "dev_02_reencode.mp4")
    assert (v["outcome"], v["reason_code"]) == ("MATCHES", "ENDORSEMENT_SOURCE_SAME")


def test_clip_not_in_the_index_is_no_record_never_matches():
    body, v = upload_and_check(MEDIA / "unindexed" / "dev_new_1.mp4")
    assert body["match"]["source_found"] is False
    assert (v["outcome"], v["reason_code"]) == ("NO_RECORD", "ENDORSEMENT_NO_SOURCE")


def test_endorsement_messages_never_call_a_video_fake_genuine_or_real():
    for lang, msgs in TEMPLATES.items():
        for code in ("ENDORSEMENT_SOURCE_SAME", "ENDORSEMENT_WORDS_CHANGED", "ENDORSEMENT_NO_SOURCE"):
            text = json.dumps(msgs[code], ensure_ascii=False).lower()
            assert not re.search(r"\b(fake|genuine|real)\b|नकली|असली|फर्जी", text), (lang, code)


def test_changed_range_renders_in_both_languages():
    _, v = upload_and_check(MEDIA / "fakes" / "dev_03_fake.mp4")

    class V:  # render() takes a verdict-like object
        reason_code, params = v["reason_code"], v["params"]

    for lang in ("en", "hi"):
        assert v["params"]["time_ranges"][0] in render(V, lang)["record"]
