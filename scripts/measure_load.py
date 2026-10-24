"""Memory and CPU check for LLM_PROVIDER=local: peak VRAM with an image and a video request at once, then seconds
per demo screenshot with the GPU hidden from the backend (CUDA_VISIBLE_DEVICES=-1) and from Ollama (num_gpu 0).

Usage: python scripts/measure_load.py   (port 8000 free, Ollama running). VRAM is the whole GPU's memory.used from
nvidia-smi, so it includes Ollama's own process; that is what has to fit on the card.
"""

import importlib.util
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("demo", ROOT / "scripts" / "demo.py")
demo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(demo)
SHOTS = [ROOT / "data" / "demo_cache" / f"demo-00{i}.png" for i in (1, 2, 3)]
LIMIT_MB = 7.8 * 1024


def vram_mb() -> int:
    q = ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"]
    return int(subprocess.run(q, capture_output=True, text=True).stdout.split()[0])


def backend(env_extra: dict):
    env = {**os.environ, "LLM_PROVIDER": "local", "EVIDENCE_KEY": demo.env_file()["EVIDENCE_KEY"],
           "HF_HUB_OFFLINE": "1", "PYTHONUNBUFFERED": "1", **env_extra}  # fmt: skip
    demo.LOGS.mkdir(parents=True, exist_ok=True)
    p = demo.start("measure_backend", [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"],
                   ROOT / "backend", env)  # fmt: skip
    if not demo.wait_for("/health ready=true", lambda: demo.health().get("ready"), 600):
        demo.stop(p)
        raise SystemExit((demo.LOGS / "measure_backend.log").read_text("utf-8")[-2000:])
    return p


def read(path: Path) -> tuple[float, dict]:
    t0 = time.perf_counter()
    cs = demo.post_file("/api/read", path.name, "image/png", path.read_bytes())
    return time.perf_counter() - t0, cs["reader"]


def main() -> int:
    print(f"idle VRAM before start: {vram_mb()} MB")
    p = backend({})
    try:
        peak, stop, out = [vram_mb()], threading.Event(), {}
        print(f"VRAM after warm-up (Ollama model, EasyOCR, CLIP, Whisper loaded): {peak[0]} MB")

        def sample():
            while not stop.is_set():
                peak.append(vram_mb())
                time.sleep(0.2)

        def image():
            out["image"] = read(SHOTS[0])

        def video():
            t0 = time.perf_counter()
            demo.post_file("/api/video", "fake.mp4", "video/mp4", (ROOT / demo.FAKE).read_bytes())
            out["video"] = time.perf_counter() - t0

        threads = [threading.Thread(target=f) for f in (sample, image, video)]
        for t in threads:
            t.start()
        for t in threads[1:]:
            t.join()
        stop.set()
        threads[0].join()
        secs, reader = out["image"]
        print(f"image and video at once: image {secs:.2f} s ({reader}), video {out['video']:.2f} s")
        verdict = "OVER" if max(peak) > LIMIT_MB else "under"
        print(f"peak VRAM: {max(peak)} MB of {LIMIT_MB:.0f} MB limit (7.8 GB) -> {verdict}")
    finally:
        demo.stop(p)
    unload = json.dumps({"model": "gemma3:4b", "keep_alive": 0}).encode()  # free the GPU before the CPU run
    demo.urllib.request.urlopen(demo.urllib.request.Request("http://127.0.0.1:11434/api/generate", unload), timeout=60)
    p = backend({"CUDA_VISIBLE_DEVICES": "-1", "KASAUTI_OLLAMA_OPTIONS": json.dumps({"num_gpu": 0}),
                 "KASAUTI_PRELOAD_VIDEO": "0"})  # fmt: skip
    try:
        print("GPU hidden (backend CUDA_VISIBLE_DEVICES=-1, Ollama num_gpu=0):")
        for shot in SHOTS:
            secs, reader = read(shot)
            print(f"  {shot.name}: {secs:.2f} s  (model {reader.get('model')}, fallback {reader.get('fallback')})")
    finally:
        demo.stop(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
