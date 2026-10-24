"""Validate the frozen test set against docs/FROZEN_SET_SPEC.md, then write or verify data/frozen/HASH.txt.

Usage: python scripts/check_frozen.py [DIR] [--example] [--skip-videos] [--rehash]
DIR defaults to data/frozen. --example checks a small sample (two of each kind) instead of the spec's minimum counts.
--skip-videos is the documented no-video scope: video counts and clip files are not required (videos/manifest.json is
still checked for shape) and HASH.txt starts with the line `scope: no-video`. Once HASH.txt exists its first line
decides the scope, so later runs need no flag (here and in scripts/run_frozen.py).
Reads only DIR and docs/formats (never the verdict rules). The only file it writes is DIR/HASH.txt: when absent and
every check passes, or with --rehash. An existing HASH.txt is compared, and any changed, added or removed file fails.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
FORMATS = ROOT / "docs" / "formats"
_claims = json.loads((FORMATS / "claims.schema.json").read_text(encoding="utf-8"))
_verdict = json.loads((FORMATS / "verdict.schema.json").read_text(encoding="utf-8"))
CLAIM = Draft202012Validator({"$defs": _claims["$defs"], "$ref": "#/$defs/claim"})
OUTCOMES = set(_verdict["$defs"]["outcome"]["enum"])
REASONS = set(_verdict["$defs"]["reason_code"]["enum"])
TYPES = {"holding", "broker", "payee", "endorsement", "platform"}
KINDS = {"injected_text", "renamed_broker", "near_duplicate_upi", "mixed_portfolio", "sourceless_video"}
VARIANTS = {"none", "recompressed", "resized", "centre_crop", "off_centre_crop", "other"}
MIN = {
    "screenshots": 60, "layouts": 6, "rule_cases": 100, "brokers": 60, "impersonations": 20,
    "payees": 15, "videos": 30, "videos_no_source": 5, "videos_off_centre": 5,
}  # fmt: skip
NO_VIDEO_LINE = "scope: no-video"
VIDEO_COUNTS = {"videos", "videos_no_source", "videos_off_centre"}  # minimums that the no-video scope skips
MIN_EXAMPLE = dict.fromkeys(MIN, 2) | {"layouts": 2, "impersonations": 1, "videos_no_source": 1, "videos_off_centre": 1}


def load(path: Path, problems: list, kind=list):
    if not path.exists():
        problems.append(f"missing file: {path.name}")
        return kind()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        problems.append(f"{path.name}: not valid UTF-8 JSON ({e})")
        return kind()
    if not isinstance(data, kind):
        problems.append(f"{path.name}: must be a JSON {kind.__name__}")
        return kind()
    return data


def need(obj: dict, keys: str, where: str, problems: list) -> bool:
    missing = [k for k in keys.split() if k not in obj]
    if missing:
        problems.append(f"{where}: missing field(s) {', '.join(missing)}")
    return not missing


def claim_ok(claim, where: str, problems: list) -> None:
    for e in CLAIM.iter_errors(claim):
        problems.append(f"{where}: claim does not match claims.schema.json ({e.message[:120]})")
        return


def verdict_ok(outcome, reason, where: str, problems: list) -> None:
    if outcome not in OUTCOMES:
        problems.append(f"{where}: outcome {outcome!r} is not MATCHES, CONTRADICTS or NO_RECORD")
    if reason not in REASONS:
        problems.append(f"{where}: unknown reason code {reason!r}")


def labelled_pngs(folder: Path, problems: list) -> dict:
    labels = load(folder / "labels.json", problems, dict)
    pngs = {p.name for p in folder.glob("*.png")} if folder.exists() else set()
    for name in sorted(pngs - set(labels)):
        problems.append(f"{folder.name}/{name}: PNG without a label")
    for name in sorted(set(labels) - pngs):
        problems.append(f"{folder.name}/labels.json: {name} has no PNG file")
    for name in sorted(pngs & set(labels)):
        if (folder / name).read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            problems.append(f"{folder.name}/{name}: not a PNG file")
    return {k: v for k, v in labels.items() if k in pngs and isinstance(v, dict)}


def expected_list(item: dict, claim_ids: set, where: str, problems: list) -> None:
    for i, e in enumerate(item.get("expected", [])):
        if need(e, "claim_id outcome reason_code", f"{where} expected[{i}]", problems):
            verdict_ok(e["outcome"], e["reason_code"], f"{where} expected[{i}]", problems)
            if e["claim_id"] not in claim_ids:
                problems.append(f"{where} expected[{i}]: claim_id {e['claim_id']!r} is not one of the case's claims")


def scope_of(root: Path) -> str | None:
    """'no-video' or 'full' from the first line of HASH.txt; None when the set has not been hashed yet."""
    h = root / "HASH.txt"
    if not h.exists():
        return None
    return "no-video" if h.read_text(encoding="utf-8").splitlines()[:1] == [NO_VIDEO_LINE] else "full"


def check(root: Path, example: bool = False, no_video: bool = False) -> tuple[list, dict]:
    """Every problem found, and the counts against their minimums (video counts are skipped when no_video)."""
    p, mins = [], MIN_EXAMPLE if example else MIN
    if not root.is_dir():
        return [f"folder not found: {root}"], {}

    shots = labelled_pngs(root / "screenshots", p)
    for name, lab in shots.items():
        if need(lab, "layout language claims", f"screenshots/{name}", p):
            if lab["language"] not in ("en", "hi"):
                p.append(f"screenshots/{name}: language must be en or hi")
            for c in lab["claims"]:
                claim_ok(c, f"screenshots/{name}", p)
    langs = {lab.get("language") for lab in shots.values()}

    cases = load(root / "rule_cases.json", p)
    types, reasons = set(), set()
    for i, case in enumerate(cases):
        where = f"rule_cases[{i}] {case.get('id', '?')}"
        if not need(case, "id claims expected", where, p):
            continue
        for c in case["claims"]:
            claim_ok(c, where, p)
            types.add(c.get("type"))
        if any(c.get("type") == "holding" for c in case["claims"]):
            if need(case, "consent_scope depositories", where, p):
                for d in case["depositories"]:
                    if d.get("status") not in ("OK", "FAILED") or "depository" not in d:
                        p.append(f"{where}: each depository needs 'depository' and status OK or FAILED")
            if "expected_summary" in case:
                reasons.add(case["expected_summary"])
                summary = str(case["expected_summary"])
                if not summary.startswith("HOLDINGS_TOTAL_") or summary not in REASONS:
                    p.append(f"{where}: expected_summary must be a HOLDINGS_TOTAL_* reason code")
        expected_list(case, {c.get("id") for c in case["claims"]}, where, p)
        reasons |= {e.get("reason_code") for e in case["expected"]}

    brokers = load(root / "brokers.json", p)
    for i, b in enumerate(brokers):
        fields = "name sebi_reg_no claims_registered expected_outcome expected_reason_code impersonates"
        if need(b, fields, f"brokers[{i}]", p):
            verdict_ok(b["expected_outcome"], b["expected_reason_code"], f"brokers[{i}] {b['name']}", p)
            if b.get("impersonates") is None and not b.get("note"):
                p.append(f"brokers[{i}] {b['name']}: a label from the real SEBI list needs a note saying so")

    payees = load(root / "payees.json", p)
    for i, py in enumerate(payees):
        where = f"payees[{i}] {py.get('id', '?')}"
        if need(py, "id claim registry expected_outcome expected_reason_code", where, p):
            claim_ok(py["claim"], where, p)
            if py["claim"].get("type") != "payee":
                p.append(f"{where}: claim type must be payee")
            verdict_ok(py["expected_outcome"], py["expected_reason_code"], where, p)

    vids = load(root / "videos" / "manifest.json", p)
    for i, v in enumerate(vids):
        where = f"videos[{i}] {v.get('file', '?')}"
        if need(v, "file expected_source expected_changed variant", where, p):
            f = root / "videos" / v["file"]
            if not f.is_file():
                if not no_video:
                    p.append(f"{where}: clip file not found in videos/")
            elif f.suffix.lower() not in (".mp4", ".mov", ".webm") or f.stat().st_size > 20 * 1024 * 1024:
                p.append(f"{where}: must be MP4, MOV or WebM under 20 MB")
            if v["variant"] not in VARIANTS:
                p.append(f"{where}: variant must be one of {sorted(VARIANTS)}")

    adv = labelled_pngs(root / "adversarial", p)
    for name, lab in adv.items():
        where = f"adversarial/{name}"
        if need(lab, "kind claims expected", where, p):
            if lab["kind"] not in KINDS:
                p.append(f"{where}: kind must be one of {sorted(KINDS)}")
            for c in lab["claims"]:
                claim_ok(c, where, p)
            expected_list(lab, {c.get("id") for c in lab["claims"]}, where, p)

    counts = {
        "screenshots": len(shots), "layouts": len({lab.get("layout") for lab in shots.values()}),
        "rule_cases": len(cases), "brokers": len(brokers),
        "impersonations": sum(1 for b in brokers if b.get("impersonates")), "payees": len(payees),
        "videos": len(vids), "videos_no_source": sum(1 for v in vids if v.get("expected_source", 0) is None),
        "videos_off_centre": sum(1 for v in vids if v.get("variant") == "off_centre_crop"),
    }  # fmt: skip
    for k, n in counts.items():
        if n < mins[k] and not (no_video and k in VIDEO_COUNTS):
            p.append(f"count: {k} {n}, need at least {mins[k]}")
    if not {"en", "hi"} <= langs:
        p.append(f"screenshots: need both en and hi, have {sorted(x for x in langs if x)}")
    if not example:
        for what, have, want in (
            ("claim types in rule_cases", types, TYPES),
            ("reason codes in rule_cases", reasons, REASONS),
            ("adversarial kinds", {lab.get("kind") for lab in adv.values()}, KINDS),
        ):
            if want - have:
                p.append(f"coverage: {what} missing {', '.join(sorted(want - have))}")
    return p, counts


def hash_lines(root: Path) -> list[str]:
    files = sorted(f.relative_to(root).as_posix() for f in root.rglob("*") if f.is_file() and f.name != "HASH.txt")
    return [f"{hashlib.sha256((root / f).read_bytes()).hexdigest()}  {f}" for f in files]


def hash_text(lines: list[str], no_video: bool = False) -> str:
    body = "\n".join([NO_VIDEO_LINE, *lines] if no_video else lines) + "\n"
    return body + f"combined  {hashlib.sha256(body.encode()).hexdigest()}\n"


def verify_hash(root: Path) -> list[str]:
    old = [
        x
        for x in (root / "HASH.txt").read_text(encoding="utf-8").splitlines()
        if not x.startswith(("combined", "scope:"))
    ]
    old_d, new_d = (dict(x.split("  ", 1)[::-1] for x in lines) for lines in (old, hash_lines(root)))
    p = [f"hash: {f} changed since HASH.txt" for f in sorted(old_d.keys() & new_d.keys()) if old_d[f] != new_d[f]]
    p += [f"hash: {f} added after HASH.txt" for f in sorted(new_d.keys() - old_d.keys())]
    return p + [f"hash: {f} removed after HASH.txt" for f in sorted(old_d.keys() - new_d.keys())]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dir", nargs="?", default=str(ROOT / "data" / "frozen"))
    ap.add_argument("--example", action="store_true", help="two of each kind instead of the spec's minimum counts")
    ap.add_argument("--skip-videos", action="store_true", help="no-video scope: clips are not required (see top)")
    ap.add_argument("--rehash", action="store_true", help="write a new HASH.txt for a deliberate new version")
    a = ap.parse_args(argv)
    root = Path(a.dir)
    scope = scope_of(root)
    # a hashed set keeps its scope; only --rehash (a deliberate new version) may change it
    no_video = a.skip_videos if a.rehash or scope is None else scope == "no-video"
    problems, counts = check(root, a.example, no_video)
    hashed = scope is not None
    if hashed and not a.rehash:
        problems += verify_hash(root)
        if a.skip_videos and scope == "full":
            problems.append("scope: HASH.txt is full scope; --skip-videos cannot weaken it (use --rehash)")
    mins = MIN_EXAMPLE if a.example else MIN
    print(f"{root}{' (EXAMPLE mode: minimum counts are 2 of each, not the spec)' if a.example else ''}")
    print(f"scope: {'no-video (video counts and clips not required)' if no_video else 'full'}")
    for k, n in counts.items():
        mark = "skip" if no_video and k in VIDEO_COUNTS else "ok  " if n >= mins[k] else "LOW "
        print(f"  {mark} {k:18} {n:>4} / {mins[k]}")
    for x in problems:
        print(f"  MISSING/WRONG: {x}")
    if problems:
        print(f"FROZEN SET NOT OK: {len(problems)} problem(s)")
        return 1
    if not hashed or a.rehash:
        (root / "HASH.txt").write_text(hash_text(hash_lines(root), no_video), encoding="utf-8", newline="\n")
        print("wrote HASH.txt")
    print(f"{(root / 'HASH.txt').read_text(encoding='utf-8').splitlines()[-1]}")
    print("FROZEN SET OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
