"""Source-match evaluation over every dev fake, variant, re-encode and unindexed clip, with the network disabled.

Usage: python scripts/video_eval.py   (exit 1 if top-1 < 90%, any unindexed clip is not NO_RECORD,
                                       any miss is MATCHES, or a source search takes 5 s or more)
       python scripts/video_eval.py data/media/clips/labels.csv [--only s05,nosrc_01] [--out docs/VIDEO_EVAL]
         the team's own test clips (scripts/make_test_clips.py): per-clip lines, a summary by type and, with --out,
         a Markdown report and its JSON. Exit 1 if a no-source clip is not NO_RECORD or an unchanged clip whose
         source was found is reported as changed.
Each clip goes through comparators/video.match and the real rules.endorsement. The first form runs the dev clips.
"""

import argparse
import csv
import json
import os
import re
import socket
import statistics
import sys
import time
from collections import Counter
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


def secs(rng: str) -> tuple[int, int]:
    a, b = (int(m) * 60 + int(s) for m, s in re.findall(r"(\d+):(\d\d)", rng))
    return a, b


def summarise(res: list[dict]) -> list[str]:
    def rate(xs, key):
        return f"{sum(x[key] for x in xs)}/{len(xs)}"

    def fired(xs):  # which signal found the source: visual, audio fingerprint, or both
        c = Counter("+".join(x["signal"]) or "none" for x in xs if x["source_ok"] and x["source_got"])
        return ", ".join(f"{k} {n}" for k, n in sorted(c.items()))

    out = [
        f"- {t}: source found top-1 {rate(xs, 'source_ok')} ({fired(xs)})"
        for t in ("reupload", "lowq", "cropped", "banner", "trimmed", "words", "words_lowq")
        if (xs := [x for x in res if x["type"] == t])
    ]
    unchanged = [x for x in res if x["type"] in ("reupload", "lowq", "cropped", "banner", "trimmed")]
    if unchanged:
        out.append(
            f"- source match over re-upload, low quality, cropped, banner, trimmed: {rate(unchanged, 'source_ok')}"
        )
    words = [x for x in res if x["words_changed_expected"]]
    if words:
        errs = [
            max(abs(x["span_got_s"][0] - x["span_expected_s"][0]), abs(x["span_got_s"][1] - x["span_expected_s"][1]))
            for x in words
            if x["span_got_s"]
        ]
        err = f", edge error median {statistics.median(errs):.1f} s, worst {max(errs):.1f} s" if errs else ""
        out.append(
            f"- words-changed clips: change found {rate(words, 'words_changed_got')}, reported span within 2 s of "
            f"the real window {rate(words, 'span_ok')}{err}"
        )
    nosrc = [x for x in res if x["type"] == "no_source"]
    if nosrc:
        n = sum(x["verdict"] == "NO_RECORD" for x in nosrc)
        out.append(
            f"- no-source clips -> NO_RECORD: {n}/{len(nosrc)}; "
            f"MATCHES: {sum(x['verdict'] == 'MATCHES' for x in nosrc)}"
        )
    fa = [x["file"] for x in res if not x["words_changed_expected"] and x["source_ok"] and x["words_changed_got"]]
    out.append(f'- false "changed words" on unchanged clips whose source was found: {len(fa)} {fa or ""}')
    search, total = [x["search_s"] for x in res], [x["total_s"] for x in res]
    out.append(
        f"- seconds per clip: source search median {statistics.median(search):.2f}, max {max(search):.2f}; "
        f"whole check (with transcript) median {statistics.median(total):.2f}, max {max(total):.2f}"
    )
    return out


def eval_labels(labels: Path, only: list[str], out: Path | None) -> int:
    rows = [r for r in csv.DictReader(labels.open(encoding="utf-8")) if r["file"].startswith(tuple(only) or "")]
    video._clip(), video._whisper()  # load once, as the API does at its first request; not part of the timings
    head = "own test set made by the team, not independent"
    print(f"{head}; device {video.device()}, whisper on {video._whisper()[1]}; network disabled for this run\n")
    res = []
    for r in rows:
        m = video.match(labels.parent / r["file"])
        verdict, code = outcome(m)
        ranges, exact = m.get("changed_ranges") or [], m.get("changed_spans_s")
        if exact is None:  # an older comparator without second-level spans
            exact = [secs(x) for x in ranges]
        span = (min(a for a, _ in exact), max(b for _, b in exact)) if exact else None
        want = (float(r["changed_from_s"]), float(r["changed_to_s"])) if r["changed_from_s"] else None
        x = {
            "file": r["file"], "type": r["type"],
            "source_expected": r["source"] or None, "source_got": m["source_clip"],
            "words_changed_expected": r["expect_words_changed"] == "1", "words_changed_got": bool(ranges),
            "span_expected_s": want, "span_got_s": span, "changed_ranges": ranges, "verdict": verdict,
            "reason_code": code, "share": m["frame_match_share"], "language": m["language"],
            "search_s": m["timings_s"]["source_search"], "total_s": m["timings_s"]["total"],
            "signal": m.get("source_signal", []), "fingerprint_hits": m.get("fingerprint_hits", 0),
        }  # fmt: skip
        x["source_ok"] = x["source_got"] == x["source_expected"]
        # ranges are whole seconds (m:ss), so 2 s either side of the real window
        x["span_ok"] = bool(span and want and want[0] - 2 <= span[0] and span[1] <= want[1] + 2)
        res.append(x)
        print(
            f"{r['file']:20} {str(x['source_expected']):8}-> {str(x['source_got']):8} share {x['share']:.2f} "
            f"fp {x['fingerprint_hits']:4} {'+'.join(x['signal']) or '-':24} | "
            f"changed {int(x['words_changed_expected'])}->{int(x['words_changed_got'])} {want or ''} -> "
            f"{' '.join(ranges)} | {verdict} {code} | {x['search_s']} s / {x['total_s']} s"
        )
    lines = summarise(res)
    print("\n" + "\n".join(lines))
    nosrc_bad = [x for x in res if x["type"] == "no_source" and x["verdict"] != "NO_RECORD"]
    false_alarm = [x for x in res if not x["words_changed_expected"] and x["source_ok"] and x["words_changed_got"]]
    if out:
        table = [
            "| clip | type | source exp -> got | signal | changed exp -> got | span exp (s) | span got | verdict | "
            "reason |",
            "|---|---|---|---|---|---|---|---|---|",
        ] + [
            f"| {x['file']} | {x['type']} | {x['source_expected'] or '-'} -> {x['source_got'] or '-'} | "
            f"{' + '.join(x['signal']) or '-'} | "
            f"{int(x['words_changed_expected'])} -> {int(x['words_changed_got'])} | "
            f"{'{:.1f}-{:.1f}'.format(*x['span_expected_s']) if x['span_expected_s'] else ''} | "
            f"{', '.join(x['changed_ranges'])} | "
            f"{x['verdict']} | {x['reason_code']} |"
            for x in res
        ]
        md = [
            f"# Video evaluation: {head}",
            "",
            f"Run {time.strftime('%d %b %Y %H:%M')}, device {video.device()}, {len(res)} clips: "
            f"`python scripts/video_eval.py {labels.as_posix()}`",
            "",
            "## Summary",
            "",
            *lines,
            "",
            "## Per clip",
            "",
            *table,
            "",
        ]
        out.with_suffix(".md").write_text("\n".join(md), encoding="utf-8")
        out.with_suffix(".json").write_text(json.dumps({"note": head, "clips": res}, indent=1) + "\n", "utf-8")
        print(f"wrote {out.with_suffix('.md')} and {out.with_suffix('.json')}")
    ok = not nosrc_bad and not false_alarm
    print("PASSED" if ok else "FAILED (a no-source clip was not NO_RECORD, or an unchanged clip was called changed)")
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ap = argparse.ArgumentParser()
        ap.add_argument("labels", type=Path)
        ap.add_argument("--only", default="", help="comma-separated file-name prefixes")
        ap.add_argument("--out", type=Path, help="write OUT.md and OUT.json")
        a = ap.parse_args()
        sys.exit(eval_labels(a.labels, [x for x in a.only.split(",") if x], a.out))
    sys.exit(main())
