"""Video source check (FR-6): which indexed official clip a video re-uses, at what offset, and which words changed.

Two signals find the source. Visual: frames at 1 fps get an open_clip ViT-B/32 embedding; most query frames must
match one clip AND agree on one time offset (look-alike slides do not agree on an offset). Audio: a landmark
fingerprint of the soundtrack (comparators/audio.py) must line up with one clip at one offset. Either one finds the
source; if both fire on different clips the source is not found. Whether words changed is decided from the audio
alone (aligned log-mel frames above a calibrated noise floor); faster-whisper only quotes the words in those spans.
Weights load from models/ only; set KASAUTI_ALLOW_DOWNLOAD=1 once (scripts/fetch_video_models.py) to fetch them.
"""

import json
import os
import statistics
import subprocess
import time
from functools import cache
from pathlib import Path

import numpy as np
from PIL import Image

from app.comparators import audio

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


def transcribe(path: Path, language: str | None = None, pcm: np.ndarray | None = None) -> tuple[list[dict], str]:
    """Words with times, and the language used: the given one, else whichever of the app's two (en, hi) is likelier."""
    pcm = audio.load(path) if pcm is None else pcm
    model, _ = _whisper()
    if language is None:  # free detection labels some Hindi speech as Urdu and writes it in Urdu script
        probs = dict(model.detect_language(pcm)[2])
        language = max(("en", "hi"), key=lambda k: probs.get(k, 0.0))
    # temperature 0 only: the default fallback re-samples low-confidence audio at random
    segments, _ = model.transcribe(pcm, word_timestamps=True, beam_size=5, language=language, temperature=0.0)
    words = [
        {"w": w.word.strip(), "start": round(w.start, 2), "end": round(w.end, 2)} for s in segments for w in s.words
    ]
    return words, language


def build_index(official: Path) -> dict:
    INDEX.mkdir(parents=True, exist_ok=True)
    clips, embs, owner, fp, mels = [], [], [], [], {}
    for n, f in enumerate(sorted(official.glob("*.mp4"))):
        rgb = frames(f)
        h, w = int(H * CROP), int(W * CROP)
        crops = np.stack(
            [np.array(Image.fromarray(x[(H - h) // 2 :][:h, (W - w) // 2 :][:, :w]).resize((W, H))) for x in rgb]
        )
        embs += [embed(rgb), embed(crops)]
        owner += [(n, t) for t in range(len(rgb))] * 2
        pcm = audio.load(f)
        h, t = audio.fingerprint(pcm)
        fp.append(np.stack([h, np.full(len(h), n), t], 1))
        mels[f"mel{n}"] = audio.logmel(pcm).astype(np.float16)
        words, lang = transcribe(f, pcm=pcm)
        clips.append({"clip": f.name, "frames": len(rgb), "phash": phashes(rgb), "words": words, "lang": lang})
    np.save(INDEX / "embeddings.npy", np.concatenate(embs).astype(np.float16))
    np.save(INDEX / "owner.npy", np.array(owner, dtype=np.int32))
    fp = np.concatenate(fp)
    fp = fp[np.argsort(fp[:, 0], kind="stable")]
    np.savez(INDEX / "audio.npz", fp_hash=fp[:, 0], fp_clip=fp[:, 1], fp_t=fp[:, 2], **mels)
    (INDEX / "clips.json").write_text(json.dumps(clips) + "\n", encoding="utf-8")
    _index.cache_clear()
    return {"clips": len(clips), "frames": len(owner) // 2, "words": sum(len(c["words"]) for c in clips)}


@cache
def _index():
    clips = json.loads((INDEX / "clips.json").read_text(encoding="utf-8"))
    sound = dict(np.load(INDEX / "audio.npz"))  # an index built before the audio checks fails here: rebuild it
    return clips, np.load(INDEX / "embeddings.npy").astype(np.float32), np.load(INDEX / "owner.npy"), sound


def _ts(s: float) -> str:
    return f"{int(s) // 60}:{int(s) % 60:02d}"


def _visual(rgb: np.ndarray, E: np.ndarray, owner: np.ndarray) -> tuple[int | None, float | None, float, float]:
    """(clip, offset s, share of frames agreeing on it, mean cosine) from the frame embeddings."""
    q = embed(rgb)
    sims = q @ E.T
    best = sims.argmax(axis=1)
    cos = sims[np.arange(len(q)), best]
    votes = [
        (int(owner[j][0]), int(owner[j][1]) - i)
        for i, (j, c) in enumerate(zip(best, cos, strict=True))
        if c >= FRAME_COS
    ]
    if not votes:
        return None, None, 0.0, 0.0
    clip_n = statistics.mode(v[0] for v in votes)
    offset = statistics.median(v[1] for v in votes if v[0] == clip_n)
    share = sum(1 for v in votes if v[0] == clip_n and abs(v[1] - offset) <= 1) / len(q)
    return clip_n, float(offset), share, float(np.mean([c for c in cos if c >= FRAME_COS]))


def match(path: Path) -> dict:
    """Compare one clip against the footage index. The verdict rule reads source_found and transcript_same (the
    field keeps its name: it is now true when no audio span differs from the source, whatever the transcripts say)."""
    _clip()  # a one-time model load is not part of the search time
    t0 = time.perf_counter()
    clips, E, owner, sound = _index()
    rgb, pcm = frames(path), audio.load(path)
    v_clip, v_off, share, mean_cos = _visual(rgb, E, owner)
    visual = share >= MIN_SHARE
    qh, qt = audio.fingerprint(pcm)
    fp = audio.best_offset(qh, qt, sound["fp_hash"], sound["fp_clip"], sound["fp_t"])
    if visual:  # does the sound support the clip the picture found? (another clip may share some of its audio)
        own = audio.best_offset(qh, qt, sound["fp_hash"], sound["fp_clip"], sound["fp_t"], clip=v_clip)
        fp = own if own and own[2] >= audio.FP_MIN_HITS else fp
    heard = bool(fp and fp[2] >= audio.FP_MIN_HITS)
    signals = [s for s, on in (("visual", visual), ("audio_fingerprint", heard)) if on]
    # the picture of one recording and the sound of another: no single source
    found = bool(signals) and not (visual and heard and v_clip != fp[0])
    clip_n = (fp[0] if heard else v_clip) if found else None
    q_mel = audio.logmel(pcm)
    # source frame - upload frame: per upload frame from the fingerprint hits (follows a splice of a different
    # length), else one number from the picture
    offsets = audio.frame_offsets(fp[3], fp[4], len(q_mel)) if found and heard else None
    offset = (offsets[0] / audio.FPS if heard else v_off) if found else None  # where the upload starts in the source
    search_s = time.perf_counter() - t0
    words, lang = transcribe(path, clips[clip_n].get("lang") if found else None, pcm)  # in the source's language
    out = {
        "source_found": found,
        "source_clip": clips[clip_n]["clip"] if found else None,
        "source_signal": signals,
        "similarity": round(mean_cos, 3) if visual else None,
        "frame_match_share": round(share, 3),
        "fingerprint_hits": fp[2] if fp else 0,
        "offset_s": round(offset, 2) if found else None,
        "query_words": len(words),
        "language": lang,
        "transcript": " ".join(w["w"] for w in words),
    }
    if found:
        mel = sound[f"mel{clip_n}"].astype(np.float32)
        align = offsets if heard else round(offset * audio.FPS)
        spans = audio.changed_spans(audio.frame_distance(q_mel, mel, align, np.unique(fp[3]) if heard else None))

        def local(t):  # offset in seconds at upload time t
            return offsets[min(int(t * audio.FPS), len(offsets) - 1)] / audio.FPS if heard else offset

        def said(ws, a, b):  # Whisper only quotes the words inside a span the audio flagged
            return " ".join(w["w"] for w in ws if a <= (w["start"] + w["end"]) / 2 <= b)

        out |= {
            "transcript_same": not spans,
            "changed_ranges": [f"{_ts(a)}-{_ts(b)}" for a, b in spans],
            "changed_spans_s": spans,
            "quote": " … ".join(said(words, a, b) for a, b in spans),
            "original_quote": " … ".join(said(clips[clip_n]["words"], a + local(a), b + local(b)) for a, b in spans),
        }
    out["timings_s"] = {"source_search": round(search_s, 2), "total": round(time.perf_counter() - t0, 2)}
    return out
