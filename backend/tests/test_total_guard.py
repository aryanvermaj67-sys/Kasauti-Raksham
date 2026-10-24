"""Guard decision: the local reader nulls a total that disagrees with its own holdings. What does the customer get?"""

import json

from app.reader import local
from tests.test_local_reader import MODEL_OUT, OCR, SHA, run_check

AD_TOTAL = 990000000  # the ad claims ₹99 crore; its own three lines add up to ₹3.98 crore


def test_inconsistent_ad_total_changes_no_verdict_only_the_shown_claimed_value(monkeypatch):
    monkeypatch.setattr(local, "_ask", lambda *a: json.dumps({**MODEL_OUT, "portfolio_total_inr": AD_TOTAL}))
    nulled = local.read_text(OCR + f"\nTotal value Rs. {AD_TOTAL}", SHA)  # the ad prints ₹99 crore
    kept = nulled.model_copy(update={"portfolio_total_inr": AD_TOTAL})  # as if the guard did not exist
    a, b = (run_check(cs, "SYN-C0001", "consent-mock-1")[0] for cs in (nulled, kept))
    print(f"\nguarded: total {nulled.portfolio_total_inr}, summary {a.summary[0].model_dump()}")
    print(f"unguarded: total {kept.portfolio_total_inr}, summary {b.summary[0].model_dump()}")
    for v in a.verdicts:
        print(f"  {v.claim_type} {v.outcome} {v.reason_code}")
    assert nulled.portfolio_total_inr is None
    assert [(v.outcome, v.reason_code) for v in a.verdicts] == [(v.outcome, v.reason_code) for v in b.verdicts]
    assert a.summary[0].reason_code == b.summary[0].reason_code == "HOLDINGS_TOTAL_NONE_FOUND"
    # the only difference: the customer is shown the sum of the lines, not the ad's ₹99 crore
    assert a.summary[0].params["claimed_value_inr"] == 39800000
    assert b.summary[0].params["claimed_value_inr"] == AD_TOTAL
