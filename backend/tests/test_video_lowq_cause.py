"""Why the low-quality copies (360p, CRF 36) found no source before the audio fingerprint: not frame sampling, aspect
or scaling (a 360p copy at good quality embeds almost exactly like the source) but heavy compression on top of the
small size, which pushes most frame embeddings under the per-frame cut-off. Uses the first indexed source clip;
skipped where media or models are absent (all git-ignored)."""

import subprocess

import numpy as np
import pytest

from app.comparators import video
from tests.helpers import ROOT

SOURCES = sorted((ROOT / "data" / "media" / "official").glob("*.mp4"))
pytestmark = pytest.mark.skipif(
    not SOURCES or not (ROOT / "models" / "open_clip").exists(), reason="source clips or CLIP weights not here"
)


def same_time_cosines(src, copy):
    a, b = video.frames(src), video.frames(copy)
    assert len(a) == len(b)  # 1 fps sampling gives the same instants in both
    return (video.embed(a) * video.embed(b)).sum(1)


def test_the_cause_is_compression_not_size_or_sampling(tmp_path):
    def copy(name, crf):
        out = tmp_path / name
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(SOURCES[0]), "-vf", "scale=-2:360"]
        subprocess.run([*cmd, "-c:v", "libx264", "-crf", crf, "-an", str(out)], check=True)
        return out

    clean, low = (
        same_time_cosines(SOURCES[0], copy("q18.mp4", "18")),
        same_time_cosines(SOURCES[0], copy("q36.mp4", "36")),
    )
    assert np.median(clean) >= 0.99  # small size alone: same picture to CLIP
    assert np.median(low) < np.median(clean) - 0.02  # compression is what moves the embedding
    assert np.mean(low >= video.FRAME_COS) < video.MIN_SHARE  # so the visual signal alone could not find the source
