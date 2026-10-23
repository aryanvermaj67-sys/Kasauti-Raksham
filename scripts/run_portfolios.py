"""Run every synthetic portfolio through aa_mock + holdings rules and compare with its expected labels.

Usage: python scripts/run_portfolios.py   (exit 1 on any miss; fix the rule, never the label)
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.connectors import aa_mock  # noqa: E402
from app.schemas.claims import HoldingClaim  # noqa: E402
from app.verdict import rules  # noqa: E402


def main():
    files = sorted((ROOT / "data" / "synthetic" / "portfolios").glob("P*.json"))
    correct, claims = 0, 0
    for f in files:
        case = json.loads(f.read_text(encoding="utf-8"))
        aa = aa_mock.fetch(case["customer_id"], "consent-mock-eval")
        misses = []
        for i, (c, want) in enumerate(zip(case["app_claims"], case["expected"], strict=True), 1):
            v = rules.holding(HoldingClaim(id=f"c{i}", type="holding", fields=c), aa)
            claims += 1
            if (v.outcome, v.reason_code) != (want["outcome"], want["reason_code"]):
                misses.append(
                    f"c{i} {c['isin']}: got {v.outcome}/{v.reason_code}, want {want['outcome']}/{want['reason_code']}"
                )
        correct += not misses
        for m in misses:
            print(f"MISS {case['case_id']} ({case['category']}) {m}")
    print(f"{correct}/{len(files)} correct ({claims} holding claims)")
    return 0 if correct == len(files) else 1


if __name__ == "__main__":
    sys.exit(main())
