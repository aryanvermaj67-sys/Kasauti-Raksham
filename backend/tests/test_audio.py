"""comparators/audio.py on synthetic sound (no media, no models): fingerprint and the changed-span aligner."""

import subprocess
import tempfile
from pathlib import Path

import numpy as np

from app.comparators import audio

SR = audio.SR


def recording(seed, seconds=20.0):
    """Speech-like bursts: harmonic stacks with random pitch, length and gaps, over a quiet room noise."""
    rng = np.random.default_rng(seed)
    out = rng.normal(0, 0.003, int(seconds * SR)).astype(np.float32)
    t = 0
    while t < len(out) - SR // 2:
        n = int(rng.uniform(0.08, 0.3) * SR)
        f0, tt = rng.uniform(110, 280), np.arange(n) / SR
        voiced = sum(np.sin(2 * np.pi * f0 * h * tt) / h for h in range(1, 10))
        breath = np.convolve(rng.normal(0, 1, n), np.ones(4) / 4, "same")  # broadband, like real speech
        burst = (voiced + 0.5 * breath) * np.hanning(n)
        out[t : t + n] += (burst * rng.uniform(0.2, 0.6)).astype(np.float32)
        t += n + int(rng.uniform(0.02, 0.2) * SR)
    return out


def recompress(a, gain=0.5):
    """A real lossy re-encode (AAC 48 kbit/s through ffmpeg) at a different loudness."""
    with tempfile.TemporaryDirectory() as tmp:
        raw, m4a = Path(tmp) / "a.f32", Path(tmp) / "a.m4a"
        (a * gain).astype(np.float32).tofile(raw)
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(raw)]
        subprocess.run([*cmd, "-c:a", "aac", "-b:a", "48k", str(m4a)], check=True)
        out = audio.load(m4a)
    return np.pad(out, (0, max(0, len(a) - len(out))))[: len(a)]


def index(*recs):
    fps = [audio.fingerprint(r) for r in recs]
    h = np.concatenate([f[0] for f in fps])
    c = np.concatenate([np.full(len(f[0]), n) for n, f in enumerate(fps)])
    t = np.concatenate([f[1] for f in fps])
    o = np.argsort(h, kind="stable")
    return h[o], c[o], t[o]


def test_fingerprint_finds_the_recording_and_the_offset_after_a_re_encode():
    src, other = recording(1), recording(2)
    q = recompress(src[5 * SR : 15 * SR])  # a 10 s excerpt starting 5 s in
    clip, offset, hits, same, _ = audio.best_offset(*audio.fingerprint(q), *index(other, src))
    assert clip == 1 and abs(offset - 5 * audio.FPS) <= 1 and hits >= audio.FP_MIN_HITS
    assert len(same) and same.max() < len(q) / audio.HOP  # the matched frames are upload frames


def test_fingerprint_does_not_match_a_different_recording_of_the_same_kind():
    q = recompress(recording(3)[: 10 * SR])
    r = audio.best_offset(*audio.fingerprint(q), *index(recording(1), recording(2)))
    assert r is None or r[2] < audio.FP_MIN_HITS


def test_aligner_flags_nothing_on_a_re_encode_or_a_trimmed_copy():
    src = recording(4)
    s = audio.logmel(src)
    assert audio.changed_spans(audio.frame_distance(audio.logmel(recompress(src)), s, 0)) == []
    trimmed = recompress(src[3 * SR :])
    assert audio.changed_spans(audio.frame_distance(audio.logmel(trimmed), s, round(3 * audio.FPS))) == []


def test_aligner_flags_the_replaced_span_only():
    src = recording(5)
    q = recompress(src).copy()
    q[8 * SR : 12 * SR] = recompress(recording(6))[: 4 * SR]  # 8-12 s replaced by other "speech"
    spans = audio.changed_spans(audio.frame_distance(audio.logmel(q), audio.logmel(src), 0))
    assert len(spans) == 1 and abs(spans[0][0] - 8) <= 0.5 and abs(spans[0][1] - 12) <= 0.5, spans


def test_aligner_absorbs_a_small_misalignment_of_the_offset():
    src = recording(7)
    q = recompress(src[int(2.1 * SR) :])  # the source search said 2 s; the true cut is 2.1 s
    assert audio.changed_spans(audio.frame_distance(audio.logmel(q), audio.logmel(src), round(2 * audio.FPS))) == []


def test_short_runs_above_the_floor_are_not_a_change():
    d = np.zeros(500, np.float32)
    d[100:140] = 1.0  # 0.8 s, under MIN_RUN_S
    assert audio.changed_spans(d) == []
    d[300:400] = 1.0  # 2 s
    assert audio.changed_spans(d) == [[6.0, 8.0]]


def test_more_than_half_replaced_still_gives_one_span_when_the_unchanged_frames_are_known():
    src = recording(8)
    q = recompress(src).copy()
    q[4 * SR : 16 * SR] = recompress(recording(9))[: 12 * SR]  # 12 of 20 s replaced
    _, _, _, t, off = audio.best_offset(*audio.fingerprint(q), *index(src))
    qm = audio.logmel(q)
    spans = audio.changed_spans(
        audio.frame_distance(qm, audio.logmel(src), audio.frame_offsets(t, off, len(qm)), np.unique(t))
    )
    assert len(spans) == 1 and abs(spans[0][0] - 4) <= 0.5 and abs(spans[0][1] - 16) <= 0.5, spans


def test_a_splice_of_a_different_length_flags_only_the_splice():
    """Words replaced by a longer sentence: everything after it shifts in time but is still the original."""
    src = recording(10)
    new = recompress(recording(11))[: int(4.5 * SR)]
    q = np.concatenate([recompress(src)[: 6 * SR], new, recompress(src)[9 * SR :]])  # 3 s out, 4.5 s in
    _, _, _, t, off = audio.best_offset(*audio.fingerprint(q), *index(src))
    qm = audio.logmel(q)
    offs = audio.frame_offsets(t, off, len(qm))
    assert offs[0] == 0 and abs(offs[-1] - (-1.5 * audio.FPS)) <= 1  # the tail sits 1.5 s later in the upload
    spans = audio.changed_spans(audio.frame_distance(qm, audio.logmel(src), offs, np.unique(t)))
    assert len(spans) == 1 and abs(spans[0][0] - 6) <= 0.5 and abs(spans[0][1] - 10.5) <= 0.5, spans


def test_best_offset_can_be_asked_about_one_clip():
    src, other = recording(12), recording(13)
    q = recompress(src[: 8 * SR])
    r = audio.best_offset(*audio.fingerprint(q), *index(src, other), clip=1)
    assert r is None or r[2] < audio.FP_MIN_HITS  # the other clip has nothing of it
