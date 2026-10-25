"""Demo-day preflight: one line per check, then GO or NO-GO with exactly what to fix.

Usage: python scripts/preflight.py   (or scripts/preflight.ps1). Run it after starting backend and frontend.
GPU rule: before the backend loads its models, 4 GB must be free. Once /health says ready the models already hold
their memory, so the rule is the headroom an image and a video request at once needed on top of the warm-up
(7181 - 5659 = 1522 MB measured 24 Oct by scripts/measure_load.py), rounded to 1.6 GB.
"""

import json
import os
import socket
import sqlite3
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OLLAMA = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
EASYOCR = Path(os.environ.get("EASYOCR_MODULE_PATH", Path.home() / ".EasyOCR")) / "model"
WEIGHTS = {
    "EasyOCR detector": EASYOCR / "craft_mlt_25k.pth",
    "EasyOCR Hindi/English": EASYOCR / "devanagari.pth",
    "CLIP ViT-B/32": ROOT / "models" / "open_clip" / "models--laion--CLIP-ViT-B-32-laion2B-s34B-b79K",
    "Whisper small": ROOT / "models" / "whisper" / "models--Systran--faster-whisper-small",
    "footage index": ROOT / "data" / "footage_index" / "audio.npz",  # with the audio fingerprints
}
FONT = ROOT / "frontend" / "node_modules" / "@fontsource" / "noto-sans-devanagari" / "files"


def get(url: str, timeout=3):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.status, r.read()


def health() -> dict:
    try:
        return json.loads(get("http://127.0.0.1:8000/health")[1])
    except (OSError, ValueError):
        return {}


def gpu(ready: bool):
    need = 1.6 if ready else 4.0
    try:
        q = ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"]
        free = int(subprocess.run(q, capture_output=True, text=True, timeout=20).stdout.split()[0]) / 1024
    except (OSError, ValueError, IndexError, subprocess.TimeoutExpired):
        return False, "nvidia-smi gave no reading", "check the GPU driver, or run on CPU (slower, see DEMO_DAY.md)"
    when = "models loaded" if ready else "before models load"
    return (
        free >= need,
        f"{free:.1f} GB free ({when}, need {need} GB)",
        "close other GPU apps (games, video players, other model servers)",
    )


def ollama():
    try:
        have = {m["name"] for m in json.loads(get(f"{OLLAMA}/api/tags")[1])["models"]}
    except (OSError, ValueError, KeyError):
        return False, f"not reachable at {OLLAMA}", "start Ollama (Start menu > Ollama) or use LLM_PROVIDER=cache"
    missing = [m for m in ("gemma3:4b", "qwen2.5:3b") if m not in have]
    return (
        not missing,
        f"running; missing {missing}" if missing else "running; gemma3:4b and qwen2.5:3b",
        (f"restore the Ollama models folder from the kit ({', '.join(missing)})"),
    )


def weights():
    missing = [name for name, p in WEIGHTS.items() if not p.exists()]
    return (
        not missing,
        f"missing {missing}" if missing else "EasyOCR, CLIP, Whisper, footage index found",
        ("restore models/, data/footage_index/ and the EasyOCR folder from the kit (scripts/restore_kit.ps1)"),
    )


def ready(h: dict):
    if not h:
        return False, "backend not answering on :8000", "start the backend (DEMO_DAY.md, step 3)"
    return bool(h.get("ready")), f"ready={h.get('ready')} loading={h.get('loading')}", "wait for ready=true"


def evidence_key():
    env = ROOT / ".env"
    lines = env.read_text(encoding="utf-8").splitlines() if env.exists() else []
    key = os.environ.get("EVIDENCE_KEY") or next(
        (x.split("=", 1)[1].strip() for x in lines if x.startswith("EVIDENCE_KEY=")), ""
    )
    from cryptography.fernet import Fernet

    try:
        Fernet(key.encode())
        return True, "set (valid Fernet key)", ""
    except ValueError:
        return False, "missing or not a Fernet key", "run scripts/reset_demo.ps1 (writes a key to .env)"


def evidence_db():
    db = ROOT / "data" / "runtime" / "kasauti.db"
    if not db.exists():
        return True, "no evidence database (reset)", ""
    con = sqlite3.connect(db)
    try:
        n = con.execute("SELECT count(*) FROM checks").fetchone()[0]
    except sqlite3.OperationalError:
        n = 0
    finally:
        con.close()
    return n == 0, f"{n} checks stored", "stop the backend, run scripts/reset_demo.ps1, start again"


def port(n: int, url: str):
    try:  # "localhost" tries IPv6 and IPv4: the frontend dev server may listen on ::1 only
        socket.create_connection(("localhost", n), timeout=1).close()
    except OSError:
        return True, f":{n} free", ""
    try:
        status = get(url)[0]
    except OSError as e:
        status = e
    return status == 200, f":{n} serving {url} -> {status}", f"something else holds :{n}; close it or reboot"


def font():
    files = list(FONT.glob("noto-sans-devanagari-devanagari-400-normal.woff*")) if FONT.exists() else []
    imported = "noto-sans-devanagari" in (ROOT / "frontend" / "src" / "main.tsx").read_text(encoding="utf-8")
    return (
        bool(files) and imported,
        "Noto Sans Devanagari bundled" if files else "font files not found",
        ("restore frontend/node_modules from the kit (or npm install --offline)"),
    )


def git_clean():
    out = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return not out, "clean" if not out else f"{len(out.splitlines())} changed file(s)", "commit or stash changes"


def main() -> int:
    h = health()
    checks = [
        ("GPU memory", gpu(bool(h.get("ready")))),
        ("Ollama models", ollama()),
        ("model weights", weights()),
        ("/health", ready(h)),
        ("EVIDENCE_KEY", evidence_key()),
        ("evidence DB", evidence_db()),
        ("port 8000", port(8000, "http://127.0.0.1:8000/health")),
        ("port 5173", port(5173, "http://localhost:5173/app")),
        ("Hindi font", font()),
        ("git tree", git_clean()),
    ]
    for name, (ok, detail, _) in checks:
        print(f"[{'ok' if ok else 'NO'}] {name:14} {detail}")
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    print(f"     commit         {commit.stdout.strip()}")
    fixes = [f"{name}: {fix}" for name, (ok, _, fix) in checks if not ok]
    print("GO" if not fixes else "NO-GO, fix:\n  " + "\n  ".join(fixes))
    return 0 if not fixes else 1


if __name__ == "__main__":
    sys.exit(main())
