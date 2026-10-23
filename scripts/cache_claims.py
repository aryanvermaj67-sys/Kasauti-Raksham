"""Run a real claim reader on an image and store its ClaimSet for LLM_PROVIDER=cache.

Usage: python scripts/cache_claims.py data/demo_cache/demo-001.png
Uses LLM_PROVIDER from the environment (offline if unset). The cache is only ever written by a reader;
never hand-write a file in data/demo_cache/.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
os.environ.setdefault("LLM_PROVIDER", "offline")
if os.environ["LLM_PROVIDER"] == "cache":
    raise SystemExit("LLM_PROVIDER=cache would replay the cache; pick a provider that reads the image")

from app import reader  # noqa: E402

if __name__ == "__main__":
    claimset = reader.read(Path(sys.argv[1]).read_bytes())
    path = reader.save_to_cache(claimset)
    print(f"{claimset.reader.provider} reader, {len(claimset.claims)} claims -> {path}")
