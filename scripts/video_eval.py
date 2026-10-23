"""Source-match evaluation over every dev fake, variant, re-encode and unindexed clip, with the network disabled.

Usage: python scripts/video_eval.py   (exit 1 if top-1 < 90%, any unindexed clip is not NO_RECORD,
                                       any miss is MATCHES, or a source search takes 5 s or more)
Each clip goes through comparators/video.match and the real rules.endorsement. Dev clips, not the consented set.
"""

import json
import os
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
os.environ["HF_HUB_OFFLINE"] = "1"
_connect = socket.socket.connect


def _offline(self, address):
    host = address[0] if isinstance(address, tuple) else address
    if host not in ("127.0.0.1", "::1", "localhost"):
        raise OSError(f"network disabled for this run: {address}")
    return _connect(self, address)


socket.socket.connect = _offline

from app.comparators import video  # noqa: E402
from app.schemas.claims import EndorsementClaim  # noqa: E402
from app.schemas.evidence import make_record  # noqa: E402
from app.verdict import rules  # noqa: E402


def outcome(result):
    claim = EndorsementClaim(
        id="v1", type="endorsement", fields={"person": "speaker", "quote": "", "media_sha256": "0" * 64}
    )
    v = rules.endorsement(claim, make_record("footage_index", result, mock=True))
    return v.outcome, v.reason_code


def main():
    manifest = json.loads((ROOT / "data" / "media" / "dev_manifest.json").read_text(encoding="utf-8"))
    video._clip(), video._whisper()  # load once, as the API does at its first request; not part of the timings
    print(f"device: {video.device()}; dev clips, not the consented set; network disabled for this run\n")
    rows, misses = [], []
    for item in manifest:
        r = video.match(ROOT / item["file"])
        want = Path(item["source"]).name if item["source"] else None
        got = r["source_clip"]
        verdict, code = outcome(r)
        top1 = got == want and (want is None or abs(r["offset_s"] - item["offset"]) <= 1)
        words_ok = want is None or r.get("transcript_same") == (item["changed"] is None)
        rows.append((item, r, verdict, top1, words_ok))
        if not top1 and verdict == "MATCHES":
            misses.append(f"MISS RETURNED MATCHES: {item['file']}")
        name, ms = Path(item["file"]).name, r["timings_s"]
        print(
            f"{name:24} want {str(want):11} got {str(got):11} share {r['frame_match_share']:.2f} sim {r['similarity']}"
        )
        print(f"{'':24} offset {r['offset_s']} -> {verdict} {code} changed {r.get('changed_ranges')}")
        print(f"{'':24} search {ms['source_search']} s, total with transcript {ms['total']} s")
        if item["kind"] == "fake":
            print(f"    said:     {r.get('quote')!r}\n    original: {r.get('original_quote')!r}")
    sourced = [x for x in rows if x[0]["source"]]
    unindexed = [x for x in rows if not x[0]["source"]]
    acc = sum(x[3] for x in sourced) / len(sourced)
    words = sum(x[4] for x in sourced)
    no_record = sum(x[2] == "NO_RECORD" for x in unindexed)
    worst = max(x[1]["timings_s"]["source_search"] for x in rows)
    print(f"\ntop-1 source match: {sum(x[3] for x in sourced)}/{len(sourced)} = {acc:.0%} (target >= 90%)")
    print(f"words judged right (re-encode same, fake changed): {words}/{len(sourced)}")
    print(f"unindexed clips -> NO_RECORD 'no source found': {no_record}/{len(unindexed)}")
    print(f"slowest source search: {worst:.2f} s (target < 5 s); misses returning MATCHES: {len(misses)}")
    for m in misses:
        print(m)
    ok = acc >= 0.9 and no_record == len(unindexed) and not misses and worst < 5
    print("PASSED" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
