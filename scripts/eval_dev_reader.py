"""Score the local claim reader on data/dev_reader (scripts/make_dev_reader_set.py): per-field accuracy and every error.

Usage: python -X utf8 scripts/eval_dev_reader.py --model gemma3:4b --tag before
       python -X utf8 scripts/eval_dev_reader.py --compare before after
Claims line up by (type, n-th of that type). A claim the image does not hold counts as an "extra" error; a failed
read (ReaderError) makes every field of that image wrong. Results: data/dev_reader/results/<tag>_<model>.json.
"""

import argparse
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SET = ROOT / "data" / "dev_reader"
RESULTS = SET / "results"


def norm(v):
    return " ".join(str(v).casefold().replace(".", "").split()) if isinstance(v, str) else v


def same(a, b) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return abs(a - b) <= 1
    return norm(a) == norm(b)


def by_type(claims):
    seen, out = Counter(), {}
    for c in claims:
        out[(c["type"], seen[c["type"]])] = c
        seen[c["type"]] += 1
    return out


def score(expected: dict, got: dict | None) -> tuple[dict, list[str]]:
    """field -> [right, total]; errors as text."""
    fields, errors = {}, []

    def tally(field, want, have, where):
        ok = fields.setdefault(field, [0, 0])
        ok[1] += 1
        if same(want, have):
            ok[0] += 1
        else:
            errors.append(f"{where} {field}: expected {want!r}, got {have!r}")

    got = got or {"language": None, "portfolio_total_inr": "<read failed>", "claims": []}
    tally("language", expected["language"], got["language"], "")
    if expected["guard_nulls_total"]:
        fields.setdefault("total (guard by design)", [0, 0])[1] += 1
        fields["total (guard by design)"][0] += got["portfolio_total_inr"] is None
    else:
        tally("portfolio_total_inr", expected["portfolio_total_inr"], got["portfolio_total_inr"], "")
    have = by_type(got["claims"])
    for key, c in by_type(expected["claims"]).items():
        for f, want in c["fields"].items():
            tally(f"{key[0]}.{f}", want, have.get(key, {}).get("fields", {}).get(f, "<no claim>"), f"{key[0]}#{key[1]}")
    for key in sorted(set(have) - set(by_type(expected["claims"]))):
        fields.setdefault("no extra claims", [0, 0])[1] += 1
        errors.append(f"extra {key[0]}#{key[1]}: {have[key]['fields']}")
    return fields, errors


def run(model: str, tag: str) -> None:
    os.environ["KASAUTI_LOCAL_MODEL"] = model
    sys.path.insert(0, str(ROOT / "backend"))
    import hashlib

    from app.reader import local

    local.TIMEOUT_S = 120
    expected = json.loads((SET / "expected.json").read_text(encoding="utf-8"))
    expected.pop("_note", None)
    total, rows, secs, fails = {}, {}, [], 0
    for name, exp in expected.items():
        img = (SET / name).read_bytes()
        t0 = time.perf_counter()
        try:
            cs = json.loads(local.read(img, hashlib.sha256(img).hexdigest()).model_dump_json())
        except local.ReaderError as e:
            cs, fails = None, fails + 1
            print(f"{name}: read failed: {e}")
        secs.append(time.perf_counter() - t0)
        fields, errors = score(exp, cs)
        rows[name] = {"layout": exp["layout"], "errors": errors, "model_used": cs and cs["reader"]["model"]}
        for f, (r, t) in fields.items():
            total.setdefault(f, [0, 0])
            total[f][0] += r
            total[f][1] += t
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = {"model": model, "tag": tag, "fields": total, "images": rows, "read_failures": fails,
           "seconds": [round(s, 2) for s in secs]}  # fmt: skip
    (RESULTS / f"{tag}_{model.replace(':', '_')}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    span = f"{min(secs):.1f}-{max(secs):.1f} s per image"
    print(f"\n{model} [{tag}]: {len(expected)} images, read failures {fails}, {span}")
    for f, (r, t) in sorted(total.items()):
        print(f"  {f:32} {r:>3} / {t:<3} {100 * r / t:5.1f}%")
    print("errors:")
    for name, row in rows.items():
        for e in row["errors"]:
            print(f"  {name} ({row['layout']}): {e}")


def compare(a: str, b: str) -> None:
    for f in sorted(RESULTS.glob(f"{a}_*.json")):
        x = json.loads(f.read_text(encoding="utf-8"))
        y = json.loads((RESULTS / f.name.replace(f"{a}_", f"{b}_", 1)).read_text(encoding="utf-8"))
        nerr = lambda r: sum(len(i["errors"]) for i in r["images"].values())  # noqa: E731
        print(f"\n{x['model']}: {a} -> {b}   errors {nerr(x)} -> {nerr(y)}")
        for k in sorted(set(x["fields"]) | set(y["fields"])):
            r0, t0 = x["fields"].get(k, [0, 0])
            r1, t1 = y["fields"].get(k, [0, 0])
            print(f"  {k:32} {r0:>3}/{t0:<3} -> {r1:>3}/{t1:<3}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gemma3:4b")
    ap.add_argument("--tag", default="run")
    ap.add_argument("--compare", nargs=2, metavar=("A", "B"))
    a = ap.parse_args()
    compare(*a.compare) if a.compare else run(a.model, a.tag)
