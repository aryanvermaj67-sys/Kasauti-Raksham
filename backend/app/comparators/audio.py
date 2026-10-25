"""Audio checks for the video source check. Pure numpy, no models.

- fingerprint / best_offset: landmark (peak-pair) hashes of the spectrogram, matched by one consistent time offset.
  This finds the exact recording an upload re-uses, through compression, crops and banners; another statement by the
  same speaker in the same room has different peaks and does not line up.
- frame_distance / changed_spans: once the source and offset are known, log-mel frames of the upload and the source
  are aligned (offset search, then DTW in a narrow band) and a span counts as changed only when the distance stays
  above the noise floor for the minimum duration. Words are never compared here.

FLOOR, MIN_RUN_S and FP_MIN_HITS come from scripts/calibrate_audio.py: re-encodes of the indexed SOURCE clips only
(never the altered test clips). The numbers and the run are in progress.md (Decisions log).
"""

import subprocess
from functools import cache
from pathlib import Path

import numpy as np

SR, HOP, NFFT = 16000, 320, 1024
FPS = SR / HOP  # 50 frames a second (20 ms)
SMOOTH = 25  # running median over 0.5 s before the floor test, so one click or codec glitch is not a span
BAND = 10  # DTW band: +-0.2 s of drift around the found offset
SEARCH = 50  # fine offset search: +-1 s around the offset the source search gave
# calibrated on source re-encodes (scripts/calibrate_audio.py; progress.md Decisions log, 25 Oct 2026)
FLOOR = 0.205  # 99.9th percentile of the smoothed distance over 64 re-encodes (median 0.033, max 0.240)
MIN_RUN_S = 1.02  # longest run above FLOOR in those re-encodes was 0.52 s, plus 0.5 s
FP_MIN_HITS = 8  # 2 x the best score against the other sources (4); lowest score against its own source 1023


def load(path: Path) -> np.ndarray:
    """16 kHz mono float32 via ffmpeg (faster-whisper's own PyAV decoder breaks on newer PyAV releases)."""
    cmd = ["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32)


def _spectrum(a: np.ndarray) -> np.ndarray:
    """Magnitude spectrogram, one row per 20 ms frame."""
    a = np.pad(a.astype(np.float32), (0, max(0, NFFT - len(a))))
    fr = np.lib.stride_tricks.sliding_window_view(a, NFFT)[::HOP] * np.hanning(NFFT).astype(np.float32)
    return np.abs(np.fft.rfft(fr, axis=1)).astype(np.float32)


@cache
def _melbank(n_mels: int = 64, fmin: float = 60.0, fmax: float = 3800.0) -> np.ndarray:
    # up to 3.8 kHz: a telephone-band (8 kHz) re-encode empties every band above 4 kHz (calibration, 25 Oct)
    def mel(f):
        return 2595 * np.log10(1 + f / 700)

    pts = 700 * (10 ** (np.linspace(mel(fmin), mel(fmax), n_mels + 2) / 2595) - 1)
    hz = np.fft.rfftfreq(NFFT, 1 / SR)
    lo, mid, hi = pts[:-2, None], pts[1:-1, None], pts[2:, None]
    return np.clip(np.minimum((hz - lo) / (mid - lo), (hi - hz) / (hi - mid)), 0, None).astype(np.float32)


def logmel(a: np.ndarray) -> np.ndarray:
    """64 log-mel bands per frame in dB, floored 80 dB under the clip's peak (codec noise in near-silence)."""
    p = _spectrum(a) ** 2 @ _melbank().T
    return (10 * np.log10(np.maximum(p, p.max() * 1e-8 + 1e-12))).astype(np.float32)


def _max_filter(s: np.ndarray, dt: int, df: int) -> np.ndarray:
    """Maximum over a (2dt+1) x (2df+1) neighbourhood (time, frequency); separable."""
    p = np.pad(s, ((dt, dt), (0, 0)), constant_values=-np.inf)
    m = np.lib.stride_tricks.sliding_window_view(p, 2 * dt + 1, axis=0).max(-1)
    p = np.pad(m, ((0, 0), (df, df)), constant_values=-np.inf)
    return np.lib.stride_tricks.sliding_window_view(p, 2 * df + 1, axis=1).max(-1)


def fingerprint(a: np.ndarray, fan: int = 5, max_dt: int = 63) -> tuple[np.ndarray, np.ndarray]:
    """(hashes, anchor frame) for each pair of spectral peaks: hash = (f1, f2, dt)."""
    s = np.log(_spectrum(a)[:, 6:320] + 1e-6)  # about 90 Hz to 5 kHz: speech
    if len(s) < 2:
        return np.zeros(0, np.int64), np.zeros(0, np.int32)
    peaks = (s == _max_filter(s, 7, 10)) & (s > np.percentile(s, 90))  # loudest local maxima only
    t, f = np.nonzero(peaks)  # sorted by time
    hashes, times = [], []
    for i in range(len(t)):
        j = i + 1
        n = 0
        while j < len(t) and t[j] - t[i] <= max_dt and n < fan:
            if t[j] > t[i]:
                hashes.append((int(f[i]) << 15) | (int(f[j]) << 6) | int(t[j] - t[i]))
                times.append(t[i])
                n += 1
            j += 1
    return np.array(hashes, np.int64), np.array(times, np.int32)


def best_offset(qh, qt, index_h, index_clip, index_t, clip: int | None = None):
    """(clip, offset, hits, hit_t, hit_off) for the clip most query hashes line up with, or for `clip` if given.
    offset: source frame - upload frame where most hashes agree (+-1 frame). hit_t / hit_off: upload frame and offset of
    every hash in an offset cluster of at least FP_MIN_HITS (a splice of different length gives two clusters); those
    frames are proven to be the same recording, so certainly unchanged. hits: how many such hashes (the best cluster's
    count when none reaches FP_MIN_HITS). index_h must be sorted; index_clip and index_t are in the same order."""
    lo, hi = np.searchsorted(index_h, qh, "left"), np.searchsorted(index_h, qh, "right")
    n = hi - lo
    qi = np.repeat(np.arange(len(qh)), n)
    ei = np.repeat(lo - np.cumsum(np.r_[0, n[:-1]]), n) + np.arange(n.sum())
    if clip is not None:
        qi, ei = qi[index_clip[ei] == clip], ei[index_clip[ei] == clip]
    if not len(ei):
        return None
    off = index_t[ei] - qt[qi]
    pairs, counts = np.unique(np.stack([index_clip[ei], off], 1), axis=0, return_counts=True)
    count = {(int(c), int(o)): int(k) for (c, o), k in zip(pairs, counts, strict=True)}

    def near(c, o):
        return sum(count.get((c, o + d), 0) for d in (-1, 0, 1))

    best = max(count, key=lambda co: near(*co))
    on_clip = index_clip[ei] == best[0]
    support = np.array([near(best[0], int(o)) >= FP_MIN_HITS for o in off]) & on_clip
    hits = int(support.sum()) or near(*best)
    return best[0], best[1], hits, qt[qi][support], off[support]


def frame_offsets(hit_t: np.ndarray, hit_off: np.ndarray, n: int) -> np.ndarray:
    """Offset for each of n upload frames: the offset of the nearest fingerprint hit in time."""
    order = np.argsort(hit_t, kind="stable")
    t, o = hit_t[order], hit_off[order]
    i = np.clip(np.searchsorted(t, np.arange(n)), 1, len(t) - 1) if len(t) > 1 else np.zeros(n, int)
    if len(t) > 1:
        i = np.where(np.abs(t[i - 1] - np.arange(n)) <= np.abs(t[i] - np.arange(n)), i - 1, i)
    return o[i].astype(int)


def frame_distance(q: np.ndarray, s: np.ndarray, offset, same: np.ndarray | None = None) -> np.ndarray:
    """RMS log-mel distance of each upload frame to its aligned source frame (nan where the source has none).
    q, s: logmel() of upload and source. offset: source frame - upload frame, either one number from the visual
    search (refined here by a +-1 s lag search) or one per upload frame from frame_offsets(). same: upload frames the
    fingerprint matched (known unchanged), used to measure the upload's level and EQ."""
    # both scaled by the SOURCE's band statistics: replaced speech in the upload must not rescale its untouched parts
    mu, sd = s.mean(0), s.std(0) + 1e-6
    q, s = (q - mu) / sd, (s - mu) / sd
    idx = np.arange(len(q))

    def rms(i, j):  # distance of upload frames i to source frames j (same shape), nan where j is outside the source
        i = np.broadcast_to(i, j.shape)
        ok = (j >= 0) & (j < len(s))
        d = np.full(j.shape, np.nan, np.float32)
        d[ok] = np.sqrt(((q[i[ok]] - s[j[ok]]) ** 2).mean(-1))
        return d

    if np.ndim(offset):  # per frame, from the fingerprint: already exact to a frame
        d0 = np.asarray(offset, int)
    else:  # one offset from the visual search: the lag with the smallest median distance over every 4th frame
        lags = np.arange(offset - SEARCH, offset + SEARCH + 1)
        sub = idx[::4]
        cost = [np.nanmedian(rms(sub, sub + lag)) if np.any((sub + lag >= 0) & (sub + lag < len(s))) else np.inf
                for lag in lags]  # fmt: skip
        d0 = np.full(len(q), int(lags[int(np.nanargmin(cost))]))
    j = idx + d0
    ok = (j >= 0) & (j < len(s))
    # the upload's level and EQ, per band: over the fingerprint-matched frames when there are 1 s of them (holds
    # however much was replaced), else over every frame (a median then holds while less than half was replaced)
    known = ok.copy()
    if same is not None:
        known[:] = False
        known[same[(same >= 0) & (same < len(q))]] = True
        known &= ok
    if known.sum() < FPS:
        known = ok
    if known.any():
        q = q - np.median(q[known] - s[j[known]], axis=0)
    # DTW in a band around it: steps keep pace, let the source stand still, or skip one source frame
    k = np.arange(-BAND, BAND + 1)
    c = rms(idx[:, None], j[:, None] + k[None, :])
    cdp = np.where(np.isnan(c), 1e3, c)
    acc, back = cdp.copy(), np.zeros(c.shape, np.int8)
    inf = np.full(1, np.inf, np.float32)
    for i in range(1, len(q)):
        prev = acc[i - 1]
        cand = np.stack([prev, np.r_[prev[1:], inf], np.r_[inf, prev[:-1]]])
        back[i] = cand.argmin(0)
        acc[i] = cdp[i] + cand[back[i], np.arange(len(k))]
    path = np.empty(len(q), int)
    path[-1] = int(acc[-1].argmin())
    for i in range(len(q) - 1, 0, -1):
        path[i - 1] = path[i] + (0, 1, -1)[back[i, path[i]]]
    return c[idx, path]


def smooth(dist: np.ndarray) -> np.ndarray:
    p = np.pad(dist, (SMOOTH // 2, SMOOTH // 2), constant_values=np.nan)
    w = np.lib.stride_tricks.sliding_window_view(p, SMOOTH)
    ok = ~np.isnan(w).all(1)
    out = np.full(len(dist), np.nan, np.float32)
    out[ok] = np.nanmedian(w[ok], axis=1)
    return out


def runs(mask: np.ndarray) -> list[tuple[int, int]]:
    """(first, last + 1) frame of each run of True."""
    d = np.diff(np.r_[0, mask.astype(np.int8), 0])
    return list(zip(np.flatnonzero(d == 1).tolist(), np.flatnonzero(d == -1).tolist(), strict=True))


def changed_spans(dist: np.ndarray, floor: float | None = None, min_run_s: float | None = None) -> list[list[float]]:
    """[start, end] seconds (upload time) where the smoothed distance stays above the floor for the minimum time."""
    floor, min_run_s = floor or FLOOR, min_run_s or MIN_RUN_S
    sm = smooth(dist)
    out = [[a / FPS, b / FPS] for a, b in runs(np.nan_to_num(sm, nan=0.0) > floor) if (b - a) / FPS >= min_run_s]
    merged = []
    for a, b in out:  # spans closer than the smoothing window are one change
        if merged and a - merged[-1][1] <= SMOOTH / FPS:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    return [[round(a, 2), round(b, 2)] for a, b in merged]
