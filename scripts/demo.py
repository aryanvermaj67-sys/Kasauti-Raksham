"""Run the whole demo offline: reset, start backend (LLM_PROVIDER=cache, EVIDENCE_KEY from .env) and frontend,
wait for "video models ready", then drive every Playwright flow and time the video path.

Usage: python scripts/demo.py [--cpu]   (or scripts/demo.sh / demo.ps1). Ports 8000 and 5173 must be free.
--cpu sets CUDA_VISIBLE_DEVICES=-1 for the backend. The backend runs with scripts/offline_guard on PYTHONPATH, so
any non-loopback connection fails and is counted; every browser flow aborts non-localhost requests (--offline).
Prints "demo OK offline" only if every flow passed and nothing tried to reach the network.
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / "data" / "runtime" / "demo_logs"
SHOT = ROOT / "data" / "demo_cache" / "demo-001.png"
FAKE = "data/media/fakes/dev_01_fake.mp4"
API = "http://localhost:8000"
FLOWS = [
    ("demo-001 EN", ["e2e_bank_app.py", "--lang", "en", "--offline"]),
    ("demo-001 HI", ["e2e_bank_app.py", "--lang", "hi", "--offline"]),
    ("demo-002", ["e2e_bank_app.py", "--demo", "demo-002", "--offline"]),
    ("demo-003", ["e2e_bank_app.py", "--demo", "demo-003", "--offline"]),
    ("fake clip", ["e2e_bank_app.py", "--video", FAKE, "--offline"]),
    ("reviewer approval", ["e2e_review.py"]),
    ("new UI: 8 steps x EN/HI x 3 scenarios", ["ui_screens.py"]),
]


def env_file() -> dict:
    path = ROOT / ".env"
    pairs = (line.split("=", 1) for line in path.read_text(encoding="utf-8").splitlines() if "=" in line)
    return {k.strip(): v.strip() for k, v in pairs if not k.strip().startswith("#")}


def start(name, cmd, cwd, env):
    log = (LOGS / f"{name}.log").open("w", encoding="utf-8")
    kw = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    return subprocess.Popen(cmd, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, shell=os.name == "nt", **kw)


def stop(proc):
    if os.name == "nt":  # npm and uvicorn spawn children; kill the tree
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        os.killpg(proc.pid, 15)


def wait_for(what, ok, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if ok():
            print(f"{what} after {time.time() - t0:.1f} s")
            return True
        time.sleep(1)
    print(f"timed out waiting for {what}")
    return False


def up(url):
    try:
        return urllib.request.urlopen(url, timeout=3).status == 200
    except OSError:
        return False


def health() -> dict:
    try:
        return json.loads(urllib.request.urlopen(API + "/health", timeout=3).read())
    except OSError:
        return {}


def ui_preparing() -> bool:
    """While the backend still loads models, the bank app says so and keeps Check disabled (it never errors)."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        page = p.chromium.launch().new_page()
        page.goto("http://localhost:5173/app")
        page.wait_for_selector("[data-testid=preparing]", timeout=15000)
        ok = page.locator("[data-testid=check-button]").is_disabled() and not health().get("ready")
        page.wait_for_selector("[data-testid=preparing]", state="detached", timeout=300000)
        return ok and page.locator("[data-testid=check-button]").is_enabled()


def post_file(path, name, ctype, data):
    b = uuid.uuid4().hex
    head = f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\nContent-Type: {ctype}\r\n\r\n'
    body = head.encode() + data + f"\r\n--{b}--\r\n".encode()
    req = urllib.request.Request(API + path, body, {"Content-Type": f"multipart/form-data; boundary={b}"})
    return json.loads(urllib.request.urlopen(req, timeout=300).read())


def time_video_path():
    """Same calls as the bank app: read the screenshot and upload the clip (one step), then the check after consent."""
    t0 = time.perf_counter()
    cs = post_file("/api/read", "demo-001.png", "image/png", SHOT.read_bytes())
    v = post_file("/api/video", "fake.mp4", "video/mp4", (ROOT / FAKE).read_bytes())
    quote = v["match"].get("quote") or " ".join(v["match"]["transcript"].split()[:25])
    fields = {"person": "DEV clip speaker", "quote": quote, "media_sha256": v["media_sha256"]}
    cs["claims"].append({"id": f"c{len(cs['claims']) + 1}", "type": "endorsement", "fields": fields})
    t1 = time.perf_counter()
    body = json.dumps({"claimset": cs, "customer_id": "SYN-C0001", "consent_id": "consent-mock-timing"}).encode()
    req = urllib.request.Request(API + "/api/check", body, {"Content-Type": "application/json"})
    json.loads(urllib.request.urlopen(req, timeout=300).read())
    t2 = time.perf_counter()
    return v["match"]["timings_s"], t1 - t0, t2 - t1, t2 - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cpu", action="store_true", help="hide the GPU from the backend (CUDA_VISIBLE_DEVICES=-1)")
    a = ap.parse_args()
    dead = "http://127.0.0.1:9"  # nothing listens there: any proxied (non-local) request fails
    os.environ.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "NO_PROXY": "localhost,127.0.0.1,::1"})
    os.environ.update({k: dead for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy")})
    os.environ["no_proxy"] = os.environ["NO_PROXY"]
    os.environ["PYTHONIOENCODING"] = "utf-8"  # flows print ₹ and Devanagari; a redirected Windows console is cp1252
    sys.stdout.reconfigure(encoding="utf-8")
    if subprocess.run([sys.executable, str(ROOT / "scripts" / "reset_demo.py")]).returncode:
        return 1
    dotenv = env_file()
    LOGS.mkdir(parents=True, exist_ok=True)
    guard = str(ROOT / "scripts" / "offline_guard")
    benv = {
        **os.environ,
        "LLM_PROVIDER": "cache",
        "KASAUTI_DEMO": "1",  # enables /demo/run and /demo/reset for the presenter view
        "EVIDENCE_KEY": dotenv["EVIDENCE_KEY"],
        "HF_HUB_OFFLINE": "1",
        "PYTHONPATH": os.pathsep.join(filter(None, [guard, os.environ.get("PYTHONPATH")])),
        "PYTHONUNBUFFERED": "1",
    }
    if a.cpu:
        benv["CUDA_VISIBLE_DEVICES"] = "-1"
    backend_log = LOGS / "backend.log"
    procs = [
        start("backend", [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"], ROOT / "backend", benv),
        start("frontend", ["npm", "run", "dev", "--", "--port", "5173", "--strictPort"], ROOT / "frontend", os.environ),
    ]
    results = {}
    try:
        ready = wait_for("frontend on :5173", lambda: up("http://localhost:5173/app"), 60)
        preparing = ready and ui_preparing()
        ready = ready and wait_for("/health ready=true", lambda: health().get("ready"), 300)
        if not ready:
            print(backend_log.read_text("utf-8")[-2000:])
            return 1
        print(next(line for line in backend_log.read_text("utf-8").splitlines() if "video models ready" in line))
        print(f"UI showed 'preparing' with Check disabled while models loaded: {preparing}")
        results["UI 'preparing' before ready"] = preparing
        for name, args in FLOWS:
            print(f"\n######## {name}: {' '.join(args)}")
            t0 = time.perf_counter()
            results[name] = subprocess.run([sys.executable, str(ROOT / "scripts" / args[0]), *args[1:]]).returncode == 0
            print(f"######## {name}: {'PASSED' if results[name] else 'FAILED'} in {time.perf_counter() - t0:.1f} s")
        timings, read_s, check_s, total_s = time_video_path()
        print(
            f"\nvideo path timing (API, {'cpu' if a.cpu else 'default device'}): "
            f"source search {timings['source_search']:.2f} s "
            f"(match total {timings['total']:.2f} s); read+video {read_s:.2f} s; check after consent {check_s:.2f} s; "
            f"full result {total_s:.2f} s. Targets: source search < 5 s, result < 60 s"
        )
    finally:
        for p in procs:
            stop(p)
    blocked = backend_log.read_text("utf-8").count("OFFLINE GUARD blocked")
    print(f"\nbackend network attempts blocked by the offline guard: {blocked}")
    for name, ok in results.items():
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    passed = len(results) == len(FLOWS) + 1 and all(results.values()) and not blocked
    print("demo OK offline" if passed else "demo FAILED")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
