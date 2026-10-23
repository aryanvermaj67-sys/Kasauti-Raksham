"""Security-name and broker-name normalisers are separate; ambiguous share names never pick an ISIN."""

import subprocess
import sys

import pytest

from app.connectors import isin_master, names, sebi
from app.schemas.claims import BrokerClaim, HoldingClaim
from app.verdict import rules
from tests.helpers import ROOT, render
from tests.test_rules import aa

LISTED = [n for nset in isin_master._index().values() for _, n in nset]


def test_security_normaliser_ignores_broker_word_lists(monkeypatch):
    before = [names.normalize_security(n) for n in LISTED]
    extra = {"capital", "stock", "club", "industries", "bank", "india", "services"}
    monkeypatch.setattr(names, "LEGAL_WORDS", names.LEGAL_WORDS | extra)
    monkeypatch.setattr(names, "GENERIC_WORDS", names.GENERIC_WORDS | extra)
    assert [names.normalize_security(n) for n in LISTED] == before
    assert names.normalize_security("Capital Small Finance Bank Ltd.") == "capital small finance bank"


def test_ambiguous_security_name_gives_no_record():
    name = next(n for nset in isin_master._index().values() if len({i for i, _ in nset}) > 1 for _, n in nset)
    rec = isin_master.lookup(name)
    assert rec.payload["isin"] is None and rec.payload["candidates"] > 1
    claim = HoldingClaim(
        id="c1", type="holding", fields={"instrument_name": name, "isin": None, "quantity": 1, "value_inr": 1}
    )
    v = rules.holding(claim, aa(cdsl=[("INE002A01018", 1)]), rec)
    assert (v.outcome, v.reason_code) == ("NO_RECORD", "HOLDING_NAME_AMBIGUOUS")


def test_isin_collision_check_on_full_lists():
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "isin_collisions.py")], capture_output=True, text=True)
    assert out.returncode == 0, out.stdout[-2000:]
    assert "WRONG" not in out.stdout


@pytest.mark.parametrize("lang", ["en", "hi"])
def test_broker_near_match_message(lang):
    name = "Zerodha Wealth Club"
    c = BrokerClaim(id="c1", type="broker", fields={"name": name, "sebi_reg_no": None, "claims_registered": True})
    v = rules.broker(c, sebi.lookup(name, None))
    assert (v.outcome, v.reason_code) == ("NO_RECORD", "BROKER_NEAR_MATCH")
    text = render(v, lang)
    print(f"\n[{lang}] {text['app']} | {text['record']}")
    assert v.params["near_name"] in text["record"] and v.params["near_reg_no"] in text["record"]
    assert "SEBI Check" in text["record"]
    for word in ("fake", "genuine", "real", "scam", "safe", "नकली", "असली", "फर्जी", "सुरक्षित"):
        assert word not in text["record"].lower()
