"""Compare local claim-reader models on the demo screenshots and dev samples (per field, time, VRAM).

Usage: python -X utf8 scripts/eval_local_reader.py [--cpu] [--out docs/LOCAL_READER_EVAL_GPU.md]
--cpu hides the GPU from EasyOCR (CUDA_VISIBLE_DEVICES=-1) and runs Ollama with num_gpu=0.
Expected claims: the demo cache entries (they agree with the screenshots and the rule tests) for the scored samples;
data/frozen_example labels for two tiny stress samples that are shown but not scored (the labels are illustrations,
e.g. they expect an ISIN the image does not show). Nothing here edits an expectation.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--cpu", action="store_true")
ap.add_argument("--out")
ap.add_argument("--with-video", action="store_true", help="load CLIP + Whisper first, as the demo backend does")
ap.add_argument("--models", nargs="*", default=["qwen2.5:3b", "gemma3:4b"])
args = ap.parse_args()
if args.cpu:
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    os.environ["KASAUTI_OLLAMA_OPTIONS"] = '{"num_gpu": 0}'
sys.path.insert(0, str(ROOT / "backend"))
from app.reader import local  # noqa: E402

local.TIMEOUT_S = 900 if args.cpu else 120
CACHE = ROOT / "data" / "demo_cache"
EXAMPLE = ROOT / "data" / "frozen_example" / "screenshots"
SAMPLES = {}  # name -> (path, expected, scored)
for p in sorted(CACHE.glob("demo-*.png")):
    cached = CACHE / f"{hashlib.sha256(p.read_bytes()).hexdigest()}.json"
    SAMPLES[p.name] = (p, json.loads(cached.read_text(encoding="utf-8")), True)
for name, label in json.loads((EXAMPLE / "labels.json").read_text(encoding="utf-8")).items():
    SAMPLES[name] = (EXAMPLE / name, label, False)


def same(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return abs(a - b) < 0.5
    return (a.casefold().strip() if isinstance(a, str) else a) == (b.casefold().strip() if isinstance(b, str) else b)


def score(expected, got):
    """Rows (claim, field, expected, got, ok) and the number of claims the reader invented."""
    rows, used = [], set()
    for ec in expected["claims"]:
        best, best_n = None, -1
        for i, gc in enumerate(got.claims):
            if i not in used and gc.type == ec["type"]:
                n = sum(same(v, getattr(gc.fields, k)) for k, v in ec["fields"].items())
                if n > best_n:
                    best, best_n = i, n
        used.add(best)
        gf = got.claims[best].fields if best is not None else None
        fields = ec["fields"]
        label = f"{ec['type']}:{fields.get('instrument_name') or fields.get('name') or fields.get('upi_id')}"
        for k, v in fields.items():
            g = getattr(gf, k) if gf is not None else "(claim missing)"
            rows.append((label, k, v, g, gf is not None and same(v, g)))
    total = got.portfolio_total_inr
    rows.append(
        ("portfolio", "total_inr", expected["portfolio_total_inr"], total, same(expected["portfolio_total_inr"], total))
    )
    return rows, len(got.claims) - len(used - {None})


def vram_peak(stop, peak):
    while not stop.is_set():
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True
        ).stdout
        peak[0] = max(peak[0], int(out.split()[0]))
        time.sleep(0.3)


if args.with_video:
    from app.comparators import video

    video.warm_up()
t = time.time()
local._easyocr()
ocr_load = time.time() - t
results = {}
for model in args.models:
    local.MODELS = [model]
    for name, (path, expected, _) in SAMPLES.items():
        data = path.read_bytes()
        t = time.time()
        text = local.ocr(data)
        ocr_s = time.time() - t
        peak, stop = [0], threading.Event()
        th = threading.Thread(target=vram_peak, args=(stop, peak))
        th.start()
        t = time.time()
        try:
            got, err = local.read_text(text, hashlib.sha256(data).hexdigest()), None
        except local.ReaderError as e:
            got, err = None, str(e)
        llm_s = time.time() - t
        stop.set()
        th.join()
        rows, extra = score(expected, got) if got else ([], 0)
        results[(model, name)] = dict(rows=rows, extra=extra, ocr_s=ocr_s, llm_s=llm_s, vram=peak[0], err=err)
        print(
            f"{model:11} {name:13} fields {sum(r[4] for r in rows)}/{len(rows)} extra {extra} ocr {ocr_s:.1f}s "
            f"model {llm_s:.1f}s vram {peak[0]} MiB {err or ''}",
            flush=True,
        )

scored = [n for n, (_, _, s) in SAMPLES.items() if s]
n_fields = sum(sum(len(c["fields"]) for c in SAMPLES[n][1]["claims"]) + 1 for n in scored)
lines = [
    f"# Local claim reader: {'CPU' if args.cpu else 'GPU'} run",
    "",
    f"EasyOCR load {ocr_load:.1f}s (once). Scored on {', '.join(scored)} ({n_fields} fields); "
    "ex_s* are unscored stress samples. Peak VRAM is the whole GPU, so it includes models left loaded by earlier runs.",
    "",
    "| model | fields right (scored) | claims invented | failed reads | mean OCR s | mean model s | peak VRAM MiB |",
    "|---|---|---|---|---|---|---|",
]
for model in args.models:
    rs = [results[(model, n)] for n in scored]
    right = sum(sum(r[4] for r in v["rows"]) for v in rs)
    extra, failed = sum(v["extra"] for v in rs), sum(v["err"] is not None for v in rs)
    ocr_mean, llm_mean = sum(v["ocr_s"] for v in rs) / len(rs), sum(v["llm_s"] for v in rs) / len(rs)
    peak = max(v["vram"] for v in rs)
    lines.append(f"| {model} | {right}/{n_fields} | {extra} | {failed} | {ocr_mean:.1f} | {llm_mean:.1f} | {peak} |")
lines += ["", "## Per field", "", "| sample | claim | field | expected | " + " | ".join(args.models) + " |"]
lines.append("|---|---|---|---|" + "---|" * len(args.models))
for name in SAMPLES:
    first = results[(args.models[0], name)]["rows"]
    for i, (claim, field, exp, _, _) in enumerate(first):
        cells = []
        for m in args.models:
            r = results[(m, name)]["rows"]
            cells.append(f"{'ok' if r[i][4] else 'WRONG'} {r[i][3]}" if r else f"FAILED: {results[(m, name)]['err']}")
        lines.append(f"| {name} | {claim} | {field} | {exp} | " + " | ".join(cells) + " |")
print("\n" + "\n".join(lines[:9]))
if args.out:
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
