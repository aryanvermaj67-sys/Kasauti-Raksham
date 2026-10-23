"""Index the official clips for the video source check: 1 fps pHash + embedding, Whisper transcript with word times.

Usage: python scripts/build_footage_index.py [data/media/official/]
First time only: KASAUTI_ALLOW_DOWNLOAD=1 python scripts/build_footage_index.py   (saves weights under models/)
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.comparators import video  # noqa: E402

if __name__ == "__main__":
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "media" / "official"
    t = time.perf_counter()
    counts = video.build_index(folder)
    print(f"device: {video.device()} (embeddings), {video._whisper()[1]} (whisper)")
    took = time.perf_counter() - t
    print(f"indexed {counts['clips']} clips, {counts['frames']} frames, {counts['words']} words in {took:.1f} s")
    print(f"-> {video.INDEX.relative_to(ROOT)}  (dev clips, not the consented set)")
