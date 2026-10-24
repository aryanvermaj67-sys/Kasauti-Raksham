"""Run the frozen test set (docs/FROZEN_SET_SPEC.md) and report against its hash.

Usage: python scripts/run_frozen.py [DIR] [--example]  (a set hashed with `scope: no-video` runs with no flag)
DIR defaults to data/frozen; --example runs data/frozen_example with the example's minimum counts.
1. Refuses to run unless scripts/check_frozen.py passes, including the HASH.txt comparison.
2. Rule cases, brokers and payees go straight through router.run_check, with the MOCK connectors answering from the
   case (depositories, Suspect Registry hits, @valid handles, footage). SEBI and RBI checks use the real cached lists.
3. A sourceless-video frame is made a silent 3 s clip and goes through POST /api/video (source search only), then the
   rules. Screenshots and the other adversarial images go through the real API (POST /api/read) on LLM_PROVIDER
   (default local); the adversarial claims then go through the rules like a rule case.
Writes docs/VALIDATION.md and docs/validation_results.json (…_EXAMPLE / …_example with --example). Only reads DIR.
"""

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
from collections import Counter
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("LLM_PROVIDER", "local")
from app.connectors import aa_mock, footage_index, suspect_registry, upi  # noqa: E402
from app.router.check import run_check  # noqa: E402
from app.schemas.claims import ClaimSet  # noqa: E402
from app.schemas.evidence import IST, make_record  # noqa: E402

_spec = importlib.util.spec_from_file_location("check_frozen", ROOT / "scripts" / "check_frozen.py")
check_frozen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_frozen)
OUTCOMES = ("MATCHES", "CONTRADICTS", "NO_RECORD")


def gate(root: Path, example: bool) -> tuple[list[str], str]:
    """Structure and hash problems (empty means OK to run) and the set's combined hash."""
    problems, _ = check_frozen.check(root, example, check_frozen.scope_of(root) == "no-video")
    if not (root / "HASH.txt").exists():
        return [*problems, "no HASH.txt: run scripts/check_frozen.py first"], ""
    problems += check_frozen.verify_hash(root)
    return problems, (root / "HASH.txt").read_text(encoding="utf-8").splitlines()[-1].split()[-1]


def connectors(case: dict) -> ExitStack:
    """MOCK records answered from the case, in the same RecordResponse shapes the real MOCK connectors give."""
    deps = {d["depository"]: d for d in case.get("depositories") or []}
    reg = case.get("registry") or {}
    hits = {h.strip().lower() for h in reg.get("suspect_registry_hits", [])}
    valid = {h.strip().lower() for h in reg.get("valid_upi_handles", [])}
    footage = case.get("footage")

    def fetch(customer_id, consent_id, scope=aa_mock.DEPOSITORIES):
        out = []
        for d in scope:
            e = deps.get(d, {"status": "OK", "accounts": []})
            if e["status"] == "FAILED":
                payload = {"depository": d, "error": "frozen case: depository failed"}
            else:
                accounts = [
                    {"Account": {"Summary": {"Investment": {"Holdings": {"Holding": a.get("holdings", [])}}}}}
                    for a in e.get("accounts", [])
                ]
                payload = {"depository": d, "fi_sections": ["Summary"], "accounts": accounts}
            out.append(make_record(f"aa_mock:{d}", payload, mock=True, consent_id=consent_id, status=e["status"]))
        return out

    def lookup(identifier):
        hit = {"identifier": identifier, "source": "mock: frozen case"} if identifier.strip().lower() in hits else None
        return make_record("suspect_registry", {"query": identifier, "hit": hit}, mock=True)

    def check(upi_id):
        return make_record("upi", {"query": upi_id, "valid_handle_format": upi_id.strip().lower() in valid}, mock=True)

    def footage_lookup(_sha):
        if footage is None:
            return None
        ranges = [f"{a}-{b}" for a, b in footage.get("changed_ranges", [])]
        payload = {
            "source_found": footage.get("source_clip") is not None,
            "source_clip": footage.get("source_clip"),
            "transcript_same": not ranges,
            "changed_ranges": ranges,
            "original_quote": footage.get("original_quote", ""),
        }
        return make_record("footage_index", payload, mock=True)

    stack = ExitStack()
    for target, fn in ((aa_mock, fetch), (suspect_registry, lookup), (upi, check), (footage_index, footage_lookup)):
        stack.enter_context(mock.patch.object(target, fn.__name__ if fn is not footage_lookup else "lookup", fn))
    return stack


def through_rules(case: dict, claims: list[dict]):
    cs = ClaimSet.model_validate(
        {
            "artifact_sha256": "0" * 64,
            "language": "en",
            "claims": claims,
            "portfolio_total_inr": case.get("portfolio_total_inr"),
            "reader": {"provider": "offline", "produced_at": datetime.now(IST)},
        }
    )
    with connectors(case):
        result, _ = run_check(cs, "FROZEN-CASE", "consent-frozen", tuple(case.get("consent_scope", ("CDSL", "NSDL"))))
    return {v.claim_id: v for v in result.verdicts}, (result.summary[0].reason_code if result.summary else None)


def item(kind, id_, expected, got, exp_reason, got_reason, note=""):
    return {"kind": kind, "id": id_, "expected": expected, "got": got, "expected_reason": exp_reason,
            "got_reason": got_reason, "ok": expected == got and exp_reason == got_reason, "note": note}  # fmt: skip


def rule_items(root: Path) -> list[dict]:
    out = []
    for case in json.loads((root / "rule_cases.json").read_text(encoding="utf-8")):
        verdicts, summary = through_rules(case, case["claims"])
        for e in case["expected"]:
            v = verdicts[e["claim_id"]]
            out.append(item("rule_case", f"{case['id']}/{e['claim_id']}", e["outcome"], v.outcome,
                            e["reason_code"], v.reason_code))  # fmt: skip
        if case.get("expected_summary"):
            out.append(item("rule_summary", case["id"], None, None, case["expected_summary"], summary))
    for i, b in enumerate(json.loads((root / "brokers.json").read_text(encoding="utf-8"))):
        fields = {k: b[k] for k in ("name", "sebi_reg_no", "claims_registered")}
        v = through_rules({}, [{"id": "c1", "type": "broker", "fields": fields}])[0]["c1"]
        note = f"impersonates {b['impersonates']}" if b.get("impersonates") else ""
        out.append(item("broker", f"broker[{i}] {b['name']}", b["expected_outcome"], v.outcome,
                        b["expected_reason_code"], v.reason_code, note))  # fmt: skip
    for p in json.loads((root / "payees.json").read_text(encoding="utf-8")):
        v = through_rules(p, [{**p["claim"], "id": "c1"}])[0]["c1"]
        out.append(item("payee", p["id"], p["expected_outcome"], v.outcome,
                        p["expected_reason_code"], v.reason_code))  # fmt: skip
    return out


def same(a, b) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= 1
    return str(a).strip().lower() == str(b).strip().lower() if a is not None and b is not None else a == b


def same_security(want, have) -> bool:
    """Security names match the way the app maps them to ISINs: case, punctuation and Ltd/Limited are ignored."""
    from app.connectors.names import normalize_security

    return isinstance(want, str) and isinstance(have, str) and normalize_security(want) == normalize_security(have)


def by_type(claims: list[dict]) -> dict:
    """(type, n-th of that type) -> claim, so read claims line up with labelled ones whatever ids the reader gave."""
    seen, out = Counter(), {}
    for c in claims:
        out[(c["type"], seen[c["type"]])] = c
        seen[c["type"]] += 1
    return out


def mapped_from_name(claim: dict, isin: str) -> bool:
    """True if the ISIN is what the NSE/BSE lists give for the claim's name: the app's mapping, not a misread."""
    from app.connectors import isin_master

    return isin_master.lookup(claim["fields"].get("instrument_name", "")).payload["isin"] == isin


def sourceless_items(client, frame: Path, lab: dict) -> list[dict]:
    """Make the frame a 3 s silent clip, run the real source search (POST /api/video), then the rules on the result."""
    with tempfile.TemporaryDirectory() as tmp:
        clip = Path(tmp) / "frame.mp4"
        subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-loop", "1", "-i", str(frame), "-f", "lavfi", "-i", "anullsrc=r=16000",
             "-t", "3", "-pix_fmt", "yuv420p", "-shortest", str(clip)], check=True)  # fmt: skip
        r = client.post("/api/video", files={"file": (clip.name, clip.read_bytes(), "video/mp4")})
    m = r.json()["match"] if r.status_code == 200 else {}
    footage = {"source_clip": m.get("source_clip"), "changed_ranges": m.get("changed_ranges", [])} if m else None
    verdicts = through_rules({"footage": footage}, lab["claims"])[0]
    out = []
    for e in lab["expected"]:
        v = verdicts[e["claim_id"]]
        out.append(item(f"adversarial:{lab['kind']}", f"{frame.name}/{e['claim_id']}", e["outcome"], v.outcome,
                        e["reason_code"], v.reason_code, lab.get("note", "")))  # fmt: skip
    return out


def image_items(root: Path) -> tuple[list[dict], dict]:
    from app import main
    from fastapi.testclient import TestClient

    client = TestClient(main.app)  # no `with`: the startup warm-up is not part of the test
    if os.environ["LLM_PROVIDER"] == "local":
        from app.reader import local

        local.warm_up()  # the backend does this at startup; a cold model would time out the first reads
    stats = {"screenshots": 0, "fields": 0, "fields_ok": 0, "isin_mapped": 0, "fallbacks": 0, "seconds": []}
    out, misses = [], []

    def read(path):
        t0 = time.perf_counter()
        r = client.post("/api/read", files={"file": (path.name, path.read_bytes(), "image/png")})
        stats["seconds"].append(round(time.perf_counter() - t0, 2))
        if r.status_code != 200:
            return None
        cs = r.json()
        stats["fallbacks"] += bool(cs["reader"].get("fallback"))
        return cs

    for name, lab in json.loads((root / "screenshots" / "labels.json").read_text(encoding="utf-8")).items():
        stats["screenshots"] += 1
        cs = read(root / "screenshots" / name)
        got = by_type(cs["claims"]) if cs else {}
        for key, c in by_type(lab["claims"]).items():
            for f, want in c["fields"].items():
                stats["fields"] += 1
                have = got.get(key, {}).get("fields", {}).get(f, "<not read>")
                if same(want, have) or (f == "instrument_name" and same_security(want, have)):
                    stats["fields_ok"] += 1
                elif (
                    f == "isin"
                    and want is None
                    and have not in (None, "<not read>")
                    and mapped_from_name(got[key], have)
                ):
                    stats["fields_ok"] += 1  # the image prints no ISIN; the app filled it in from the name (FR-2.7)
                    stats["isin_mapped"] += 1
                else:
                    misses.append(f"{name} {key[0]}#{key[1]} {f}: expected {want!r}, got {have!r}")
    for name, lab in json.loads((root / "adversarial" / "labels.json").read_text(encoding="utf-8")).items():
        if lab["kind"] == "sourceless_video":  # a video frame: endorsements come from the video route, not the reader
            out += sourceless_items(client, root / "adversarial" / name, lab)
            continue
        cs = read(root / "adversarial" / name)
        read_claims = [c for c in (cs["claims"] if cs else []) if c["type"] != "endorsement"]
        verdicts = through_rules(lab, read_claims)[0] if read_claims else {}
        got_by_key = {k: verdicts.get(c["id"]) for k, c in by_type(read_claims).items()}
        label_key = {c["id"]: k for k, c in by_type(lab["claims"]).items()}
        for e in lab["expected"]:
            v = got_by_key.get(label_key[e["claim_id"]])
            out.append(item(f"adversarial:{lab['kind']}", f"{name}/{e['claim_id']}", e["outcome"],
                            v.outcome if v else "NOT_READ", e["reason_code"], v.reason_code if v else None,
                            lab.get("note", "")))  # fmt: skip
    stats["field_misses"] = misses
    return out, stats


def video_section(root: Path, no_video: bool) -> list[str]:
    """Every manifest entry, as not run: this script never runs the video source check."""
    why = "no-video scope" if no_video else "run scripts/video_eval.py"
    manifest = root / "videos" / "manifest.json"
    clips = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else []
    return [
        "",
        f"## Video items ({len(clips)}): not run",
        "",
        *(f"- `{v['file']}`: not run ({why})" for v in clips),
        "",
    ]


def report(items, stats, set_hash, root, example) -> str:
    no_video = check_frozen.scope_of(root) == "no-video"
    verdict_items = [i for i in items if i["expected"] in OUTCOMES]
    matrix = Counter((i["expected"], i["got"]) for i in verdict_items)
    false_c = [i for i in verdict_items if i["got"] == "CONTRADICTS" and i["expected"] != "CONTRADICTS"]
    reason_ok = sum(i["expected_reason"] == i["got_reason"] for i in items)
    injection = [i for i in items if i["kind"] == "adversarial:injected_text"]
    fails = [i for i in items if not i["ok"]]
    secs = stats["seconds"]
    lines = [
        f"# Frozen-set validation{' (EXAMPLE set, not the frozen set)' if example else ''}",
        "",
        f"**Scope: {'no-video (video items are not run, see the end)' if no_video else 'full'}**",
        "",
        f"Set: `{root.relative_to(ROOT).as_posix()}` · combined hash `{set_hash}` · "
        f"reader LLM_PROVIDER={os.environ['LLM_PROVIDER']} · {datetime.now(IST):%d %b %Y %H:%M} IST",
        "",
        "| Expected \\ Got | MATCHES | CONTRADICTS | NO_RECORD | NOT_READ |",
        "|---|---|---|---|---|",
        *(f"| {e} | " + " | ".join(str(matrix[(e, g)]) for g in (*OUTCOMES, "NOT_READ")) + " |" for e in OUTCOMES),
        "",
        "| Measure | Result |",
        "|---|---|",
        f"| Verdict items (rule cases, brokers, payees, adversarial) | {len(verdict_items)} |",
        f"| Outcome correct | {sum(i['expected'] == i['got'] for i in verdict_items)} / {len(verdict_items)} |",
        f"| **FALSE CONTRADICTION** (expected MATCHES or NO_RECORD, got CONTRADICTS) | **{len(false_c)}** |",
        f"| reason_code correct (incl. {sum(i['kind'] == 'rule_summary' for i in items)} summaries) | "
        f"{reason_ok} / {len(items)} |",
        f"| Screenshot fields read correctly | {stats['fields_ok']} / {stats['fields']} "
        f"({stats['screenshots']} screenshots; {stats['isin_mapped']} are ISINs the app filled in from the name) |",
        f"| Reader fallbacks (local failed, offline answered) | {stats['fallbacks']} |",
        f"| Seconds per image (read) | {min(secs, default=0)}–{max(secs, default=0)} |",
        f"| Injection cases passed | {sum(i['ok'] for i in injection)} / {len(injection)} |",
        "",
        "## Injection cases",
        "",
        *(
            f"- {'ok' if i['ok'] else 'FAIL'} `{i['id']}`: expected {i['expected']} {i['expected_reason']}, "
            f"got {i['got']} {i['got_reason']}. {i['note']}"
            for i in injection
        ),  # fmt: skip
        "",
        f"## Failing items ({len(fails)} verdicts, {len(stats['field_misses'])} screenshot fields)",
        "",
        *(
            f"- `{i['kind']}` `{i['id']}`: expected {i['expected']} {i['expected_reason']}, got {i['got']} "
            f"{i['got_reason']}"
            for i in fails
        ),  # fmt: skip
        *(f"- field: {m}" for m in stats["field_misses"]),
        *video_section(root, no_video),
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dir", nargs="?")
    ap.add_argument("--example", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.dir or ROOT / "data" / ("frozen_example" if a.example else "frozen")).resolve()
    problems, set_hash = gate(root, a.example)
    if problems:
        print("REFUSED: the frozen set does not pass check_frozen.py:\n  " + "\n  ".join(problems))
        return 2
    items = rule_items(root)
    more, stats = image_items(root)
    items += more
    text = report(items, stats, set_hash, root, a.example)
    print(text)
    tag = "_EXAMPLE" if a.example else ""
    (ROOT / "docs" / f"VALIDATION{tag}.md").write_text(text, encoding="utf-8")
    results = {"set": root.name, "combined_hash": set_hash, "items": items, "reader": stats}
    (ROOT / "docs" / f"validation_results{tag.lower()}.json").write_text(
        json.dumps(results, indent=1), encoding="utf-8"
    )
    print(f"wrote docs/VALIDATION{tag}.md and docs/validation_results{tag.lower()}.json")
    return 0 if all(i["ok"] for i in items) and not stats["field_misses"] else 1


if __name__ == "__main__":
    sys.exit(main())
