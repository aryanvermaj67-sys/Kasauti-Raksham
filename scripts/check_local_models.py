"""Check the free local model stack (docs/SETUP_LOCAL_MODELS.md): exits 0 only if all four checks pass.

Usage: python scripts/check_local_models.py
Checks: Ollama reachable, both models pulled, EasyOCR imports, EasyOCR model folder holds the weights.
"""

import os
import sys
from pathlib import Path

import httpx

OLLAMA = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
MODELS = ["qwen2.5:3b", "gemma3:4b"]
EASYOCR_DIR = Path(os.environ.get("EASYOCR_MODULE_PATH", Path.home() / ".EasyOCR")) / "model"
EASYOCR_FILES = ["craft_mlt_25k.pth", "devanagari.pth"]  # detector + the Hindi/English recogniser


def ollama_models() -> list[str]:
    return [m["name"] for m in httpx.get(f"{OLLAMA}/api/tags", timeout=5).json()["models"]]


def easyocr_imports() -> None:
    import bidi
    import bidi.algorithm

    # python-bidi 0.4.2 (pure Python, the 0.6 DLL is blocked by Application Control) lacks the name easyocr imports
    bidi.get_display = getattr(bidi, "get_display", bidi.algorithm.get_display)
    import easyocr  # noqa: F401


def main() -> int:
    ok = True

    def report(name: str, passed: bool, detail: str) -> None:
        nonlocal ok
        ok &= passed
        print(f"[{'OK' if passed else 'FAIL'}] {name}: {detail}")

    have: list[str] = []
    try:
        have = ollama_models()
        report("Ollama reachable", True, OLLAMA)
    except Exception as e:
        report("Ollama reachable", False, f"cannot reach {OLLAMA} ({type(e).__name__}). Start it with `ollama serve`")
    for m in MODELS:
        detail = "present" if m in have else f"not present; run `ollama pull {m}` (needs Ollama running)"
        report(f"model {m}", m in have, detail)
    try:
        easyocr_imports()
        report("EasyOCR import", True, "ok")
    except Exception as e:
        report("EasyOCR import", False, f"{type(e).__name__}: {e}")
    missing = [f for f in EASYOCR_FILES if not (EASYOCR_DIR / f).exists()]
    report("EasyOCR models", not missing, f"{EASYOCR_DIR}" if not missing else f"missing {missing} in {EASYOCR_DIR}")
    print("local models OK" if ok else "local models NOT READY")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
