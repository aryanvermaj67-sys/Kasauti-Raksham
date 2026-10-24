"""Run every demo screenshot through the real API and compare verdicts across LLM_PROVIDER modes.

Usage:
  LLM_PROVIDER=cache python scripts/compare_reader_verdicts.py run /tmp/cache.json
  LLM_PROVIDER=local python scripts/compare_reader_verdicts.py run /tmp/local.json
  python scripts/compare_reader_verdicts.py diff /tmp/cache.json /tmp/local.json   (exit 1 if any verdict differs)
Verdicts are compared as (claim type, outcome, reason code, params); ids and evidence ids are ignored.
"""

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))


def run(out: str) -> None:
    from app import main
    from app.evidence import hashchain
    from fastapi.testclient import TestClient

    hashchain.DB = Path(tempfile.mkdtemp()) / "compare.db"  # never touch the demo's evidence DB
    hashchain.KEY_FILE = Path(tempfile.mkdtemp()) / "compare.key"
    client = TestClient(main.app)
    customers = json.loads((ROOT / "data" / "demo_cache" / "demo_customers.json").read_text(encoding="utf-8"))
    result = {}
    for demo, customer in customers.items():
        image = (ROOT / "data" / "demo_cache" / demo).read_bytes()
        r = client.post("/api/read", files={"file": (demo, image, "image/png")})
        if r.status_code != 200:
            result[demo] = {"error": f"/api/read {r.status_code}: {r.text[:200]}"}
            continue
        claimset = r.json()
        body = {"claimset": claimset, "customer_id": customer, "consent_id": "consent-mock-1"}
        checked = client.post("/api/check", json=body).json()
        result[demo] = {
            "reader": claimset["reader"],
            "verdicts": [[v["claim_type"], v["outcome"], v["reason_code"], v["params"]] for v in checked["verdicts"]],
            "summary": [[s.get("outcome"), s["reason_code"], s["params"]] for s in checked["summary"]],
        }
    Path(out).write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    for demo, r in result.items():
        print(demo, r.get("error") or f"{len(r['verdicts'])} verdicts, reader {r['reader']['provider']}")


def diff(a: str, b: str) -> int:
    ra, rb = (json.loads(Path(p).read_text(encoding="utf-8")) for p in (a, b))
    bad = 0
    for demo in ra:
        for key in ("verdicts", "summary"):
            if ra[demo].get(key) != rb[demo].get(key):
                bad += 1
                print(f"DIFFERENT {demo} {key}:\n  {a}: {ra[demo].get(key)}\n  {b}: {rb[demo].get(key)}")
    print("verdicts identical for every demo screenshot" if not bad else f"{bad} difference(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "run":
        run(sys.argv[2])
    else:
        sys.exit(diff(sys.argv[2], sys.argv[3]))
