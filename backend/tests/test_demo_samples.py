"""The cached demo screenshots give the outcome each FR-8.4 screen is built for."""

import json

import pytest

from app import reader
from app.router.check import run_check
from tests.helpers import ROOT

CACHE = ROOT / "data" / "demo_cache"
CUSTOMERS = json.loads((CACHE / "demo_customers.json").read_text())


def check(demo, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "cache")
    claimset = reader.read((CACHE / demo).read_bytes())
    return claimset, run_check(claimset, CUSTOMERS[demo], "consent-mock-1")[0]


def test_demo_002_genuine_investor_all_matches(monkeypatch):
    claimset, result = check("demo-002.png", monkeypatch)
    assert claimset.reader.provider == "offline"
    assert [c.type for c in claimset.claims].count("holding") == 4
    assert {v.outcome for v in result.verdicts} == {"MATCHES"}
    assert result.summary[0].reason_code == "HOLDINGS_TOTAL_ALL_FOUND"


def test_demo_003_nsdl_failed_every_holding_partial(monkeypatch):
    claimset, result = check("demo-003.png", monkeypatch)
    holdings = [v for v in result.verdicts if v.claim_type == "holding"]
    assert len(holdings) == 3
    assert {(v.outcome, v.reason_code) for v in holdings} == {("NO_RECORD", "HOLDING_PARTIAL_COVERAGE")}
    assert all(v.params["failed_depositories"] == ["NSDL"] for v in holdings)
    assert "CONTRADICTS" not in {v.outcome for v in result.verdicts}
    assert result.summary[0].reason_code == "HOLDINGS_TOTAL_INCOMPLETE"


@pytest.mark.parametrize("demo", sorted(CUSTOMERS))
def test_demo_cache_entries_come_from_a_reader(demo, monkeypatch):
    claimset, _ = check(demo, monkeypatch)
    assert claimset.reader.provider in {"offline", "bedrock", "anthropic"}
