"""Set the audio thresholds (comparators/audio.py) from re-encodes of the indexed SOURCE clips only.

Usage: python scripts/calibrate_audio.py [data/media/official]
Never reads the altered test clips. Each source is re-encoded several ways (bitrates, mono, MP3, resampling, louder,
quieter, trimmed start) into a temp folder; nothing in any of them is a changed word, so:
- FLOOR: 99.9th percentile of the smoothed per-frame log-mel distance over all those re-encodes;
  MIN_RUN_S: the longest run above FLOOR seen in them, plus 0.5 s (so none of them would be flagged).
- FP_MIN_HITS: twice the best fingerprint score of a source against the OTHER sources (leave-one-out: different
  statements by the same speakers, same room), checked to stay below every re-encode's score against its own source.
Prints the numbers to copy into comparators/audio.py and the Decisions log.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.comparators import audio  # noqa: E402

VARIANTS = {  # name -> (ffmpeg args before the output, start trimmed in seconds)
    "aac 32k mono": (["-c:a", "aac", "-b:a", "32k", "-ac", "1"], 0),
    "aac 48k": (["-c:a", "aac", "-b:a", "48k"], 0),
    "mp3 64k": (["-c:a", "libmp3lame", "-b:a", "64k"], 0),
    "8 kHz resample": (["-ar", "8000", "-c:a", "aac"], 0),
    "22.05 kHz resample": (["-ar", "22050", "-c:a", "aac"], 0),
    "6 dB quieter": (["-af", "volume=-6dB", "-c:a", "aac"], 0),
    "6 dB louder": (["-af", "volume=6dB", "-c:a", "aac"], 0),
    "first 5 s cut": (["-c:a", "aac"], 5),
}


def index(fps: dict, keys: list) -> tuple:
    """Sorted (hashes, clip number, frame) over the given sources, as build_index stores them."""
    h = np.concatenate([fps[k][0] for k in keys])
    c = np.concatenate([np.full(len(fps[k][0]), n) for n, k in enumerate(keys)])
    t = np.concatenate([fps[k][1] for k in keys])
    o = np.argsort(h, kind="stable")
    return h[o], c[o], t[o]


def main() -> None:
    official = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "media" / "official"
    sources = sorted(official.glob("*.mp4"))
    pcm = {f.stem: audio.load(f) for f in sources}
    mel = {k: audio.logmel(a) for k, a in pcm.items()}
    fps = {k: audio.fingerprint(a) for k, a in pcm.items()}
    smoothed, positives, negatives = [], [], []
    with tempfile.TemporaryDirectory() as tmp:
        for f in sources:
            for name, (args, cut) in VARIANTS.items():
                out = Path(tmp) / f"{f.stem}.{'mp3' if 'mp3' in name else 'm4a'}"
                pre = ["-ss", str(cut)] if cut else []
                subprocess.run(
                    ["ffmpeg", "-y", "-loglevel", "error", *pre, "-i", str(f), "-vn", *args, str(out)], check=True
                )
                a = audio.load(out)
                qh, qt = audio.fingerprint(a)
                qm = audio.logmel(a)
                own = audio.best_offset(qh, qt, *index(fps, list(fps)), clip=list(fps).index(f.stem))
                # aligned as video.match aligns a fingerprint match: per-frame offsets and the matched frames
                offs = audio.frame_offsets(own[3], own[4], len(qm)) if own and len(own[3]) else round(cut * audio.FPS)
                same = np.unique(own[3]) if own and len(own[3]) else None
                sm = audio.smooth(audio.frame_distance(qm, mel[f.stem], offs, same))
                smoothed.append(sm[~np.isnan(sm)])
                for others in (False, True):  # own index, then the index without this source
                    keys = [k for k in fps if k != f.stem] if others else list(fps)
                    r = audio.best_offset(qh, qt, *index(fps, keys))
                    hits = r[2] if r else 0
                    if others:
                        negatives.append((hits, f.stem, name))
                    else:
                        right = r and keys[r[0]] == f.stem and abs(r[1] - round(cut * audio.FPS)) <= 1
                        positives.append((hits if right else 0, f.stem, name))
                print(f"{f.stem} {name:20} max smoothed distance {sm[~np.isnan(sm)].max():.3f}  "
                      f"fp own {positives[-1][0]:4} others {negatives[-1][0]:3}")  # fmt: skip
    allsm = np.concatenate(smoothed)
    floor = float(np.percentile(allsm, 99.9))
    longest = max((b - a for s in smoothed for a, b in audio.runs(s > floor)), default=0) / audio.FPS
    neg, pos = max(negatives), min(positives)
    print(f"\n{len(smoothed)} re-encodes of {len(sources)} sources, {len(allsm)} frames")
    print(f"smoothed distance: median {np.median(allsm):.3f}, 99th {np.percentile(allsm, 99):.3f}, "
          f"99.9th {floor:.3f}, max {allsm.max():.3f}")  # fmt: skip
    print(f"FLOOR = {floor:.3f}; longest run above it {longest:.2f} s -> MIN_RUN_S = {longest + 0.5:.2f}")
    print(
        f"fingerprint: best score against other sources {neg[0]} ({neg[1]}, {neg[2]}); "
        f"lowest own-source score {pos[0]} ({pos[1]}, {pos[2]})"
    )
    fp_min = 2 * neg[0]
    print(f"FP_MIN_HITS = {fp_min}" + ("" if fp_min < pos[0] else "  WARNING: not below every own-source score"))


if __name__ == "__main__":
    main()
