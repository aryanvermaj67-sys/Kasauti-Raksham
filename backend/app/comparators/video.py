"""Video source check (FR-6): which indexed official clip a video re-uses, at what offset, and which words changed.

Frames at 1 fps get a perceptual hash and an open_clip ViT-B/32 embedding. A source is found only when most query
frames match one clip AND agree on one time offset (look-alike slides do not agree on an offset). Transcripts come
from faster-whisper small with word timestamps; changed words are reported as time ranges in the query clip.
Weights load from models/ only; set KASAUTI_ALLOW_DOWNLOAD=1 once (scripts/fetch_video_models.py) to fetch them.
"""

import difflib
import json
import os
import re
import statistics
import subprocess
import time
from functools import cache
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
MODELS = ROOT / "models"
INDEX = ROOT / "data" / "footage_index"
if os.environ.get("KASAUTI_ALLOW_DOWNLOAD") != "1":
    os.environ["HF_HUB_OFFLINE"] = "1"  # never reach the network at demo time

W, H = 320, 180
FRAME_COS = 0.96  # a frame "matches" at or above this cosine; unindexed dev clips peak at 0.945
CROP = 0.9  # official frames are also indexed as a centre crop this size (FR-6.3: crops up to a tenth)
MIN_SHARE = 0.6  # share of query frames that must match one clip at one offset (+-1 s)


@cache
def device() -> str:
    import torch

    return "cuda" if torch.cuda.is_available() else "cpu"


@cache
def _clip():
    import open_clip

    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="laion2b_s34b_b79k", cache_dir=str(MODELS / "open_clip"), device=device()
    )
    return model.eval(), preprocess


@cache
def _whisper():
    from faster_whisper import WhisperModel

    kw = {"download_root": str(MODELS / "whisper"), "local_files_only": os.environ.get("KASAUTI_ALLOW_DOWNLOAD") != "1"}
    if device() == "cuda":
        try:
            return WhisperModel("small", device="cuda", compute_type="float16", **kw), "cuda"
        except Exception:  # CTranslate2 without usable CUDA libraries: fall back to CPU
            pass
    return WhisperModel("small", device="cpu", compute_type="int8", **kw), "cpu"


def warm_up() -> None:
    """Load both models and run one tiny inference each (first CUDA calls are slow)."""
    embed(np.zeros((1, H, W, 3), np.uint8))
    model, _ = _whisper()
    list(model.transcribe(np.zeros(16000, np.float32), language="en")[0])
    _index()


def frames(path: Path) -> np.ndarray:
    """1 frame per second, scaled to W x H RGB."""
    cmd = [
        "ffmpeg",
        "-loglevel",
        "error",
        "-i",
        str(path),
        "-vf",
        f"fps=1,scale={W}:{H}",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-",
    ]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)


def embed(rgb: np.ndarray) -> np.ndarray:
    import torch
    from PIL import Image

    model, preprocess = _clip()
    batch = torch.stack([preprocess(Image.fromarray(f)) for f in rgb]).to(device())
    with torch.no_grad():
        e = model.encode_image(batch).float()
    return torch.nn.functional.normalize(e, dim=-1).cpu().numpy()


def phashes(rgb: np.ndarray) -> list[str]:
    import imagehash
    from PIL import Image

    return [str(imagehash.phash(Image.fromarray(f))) for f in rgb]


def transcribe(path: Path) -> list[dict]:
    # decode with ffmpeg (16 kHz mono float32): faster-whisper's own PyAV decoder breaks on newer PyAV releases
    cmd = ["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", "16000", "-"]
    audio = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32)
    model, _ = _whisper()
    segments, _ = model.transcribe(audio, word_timestamps=True, beam_size=5, language="en")
    return [
        {"w": w.word.strip(), "start": round(w.start, 2), "end": round(w.end, 2)} for s in segments for w in s.words
    ]


def build_index(official: Path) -> dict:
    INDEX.mkdir(parents=True, exist_ok=True)
    clips, embs, owner = [], [], []
    for n, f in enumerate(sorted(official.glob("*.mp4"))):
        rgb = frames(f)
        h, w = int(H * CROP), int(W * CROP)
        crops = np.stack(
            [np.array(Image.fromarray(x[(H - h) // 2 :][:h, (W - w) // 2 :][:, :w]).resize((W, H))) for x in rgb]
        )
        embs += [embed(rgb), embed(crops)]
        owner += [(n, t) for t in range(len(rgb))] * 2
        clips.append({"clip": f.name, "frames": len(rgb), "phash": phashes(rgb), "words": transcribe(f)})
    np.save(INDEX / "embeddings.npy", np.concatenate(embs).astype(np.float16))
    np.save(INDEX / "owner.npy", np.array(owner, dtype=np.int32))
    (INDEX / "clips.json").write_text(json.dumps(clips) + "\n", encoding="utf-8")
    _index.cache_clear()
    return {"clips": len(clips), "frames": len(owner) // 2, "words": sum(len(c["words"]) for c in clips)}


@cache
def _index():
    clips = json.loads((INDEX / "clips.json").read_text(encoding="utf-8"))
    return clips, np.load(INDEX / "embeddings.npy").astype(np.float32), np.load(INDEX / "owner.npy")


def _norm(w: str) -> str:
    return re.sub(r"[^\w']+", "", w.lower())


def _ts(s: float) -> str:
    return f"{int(s) // 60}:{int(s) % 60:02d}"


def changed_ranges(source_words: list[dict], query_words: list[dict]):
    """Word-level diff; ranges are in the query clip's time. Returns (ranges, query text, source text) of changes."""
    a, b = [_norm(w["w"]) for w in source_words], [_norm(w["w"]) for w in query_words]
    spans, said, original = [], [], []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal" or (op == "delete" and j1 in (0, len(b))):
            continue  # source words before or after the query's own start and end are a cut, not a change
        if j2 > j1:
            spans.append([query_words[j1]["start"], query_words[j2 - 1]["end"]])
        else:  # words dropped from the source: mark the point where they were
            t = query_words[min(j1, len(query_words) - 1)]["start"] if query_words else 0.0
            spans.append([t, t])
        said += [w["w"] for w in query_words[j1:j2]]
        original += [w["w"] for w in source_words[i1:i2]]
    merged = []
    for s, e in sorted(spans):
        if merged and s - merged[-1][1] <= 2:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return [f"{_ts(s)}-{_ts(e)}" for s, e in merged], " ".join(said), " ".join(original)


def match(path: Path) -> dict:
    """Compare one clip against the footage index. The verdict rule reads source_found and transcript_same."""
    _clip()  # a one-time model load is not part of the search time
    t0 = time.perf_counter()
    clips, E, owner = _index()
    rgb = frames(path)
    q = embed(rgb)
    sims = q @ E.T
    best = sims.argmax(axis=1)
    cos = sims[np.arange(len(q)), best]
    votes = [
        (int(owner[j][0]), int(owner[j][1]) - i)
        for i, (j, c) in enumerate(zip(best, cos, strict=True))
        if c >= FRAME_COS
    ]
    found, clip_n, offset, share, mean_cos = False, None, None, 0.0, 0.0
    if votes:
        clip_n = statistics.mode(v[0] for v in votes)
        offset = statistics.median(v[1] for v in votes if v[0] == clip_n)
        agree = [i for i, v in enumerate(votes) if v[0] == clip_n and abs(v[1] - offset) <= 1]
        share = len(agree) / len(q)
        mean_cos = float(np.mean([c for c in cos if c >= FRAME_COS]))
        found = share >= MIN_SHARE
    search_s = time.perf_counter() - t0
    words = transcribe(path)
    out = {
        "source_found": found,
        "source_clip": clips[clip_n]["clip"] if found else None,
        "similarity": round(mean_cos, 3) if found else None,
        "frame_match_share": round(share, 3),
        "offset_s": int(offset) if found else None,
        "query_words": len(words),
        "transcript": " ".join(w["w"] for w in words),
    }
    if found:
        lo, hi = offset - 1, offset + len(rgb) + 1
        src = [w for w in clips[clip_n]["words"] if lo <= w["start"] <= hi]
        ranges, said, original = changed_ranges(src, words)
        out |= {"transcript_same": not ranges, "changed_ranges": ranges, "quote": said, "original_quote": original}
    out["timings_s"] = {"source_search": round(search_s, 2), "total": round(time.perf_counter() - t0, 2)}
    return out
