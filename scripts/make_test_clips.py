"""Turn the team's consented recordings into the video test set (Python port of make_test_clips.sh, which never landed).

Usage: python scripts/make_test_clips.py ["IITD Videos"] ["IITD altered Audio"]
Reads the two recording folders (never changes them) and writes, all git-ignored under data/media/:
  official/s0N.mp4      sources: H.264/AAC 44.1 kHz, yuv420p, 30 fps, long side <= 1280 (the only files indexed)
  alt/s0N_alt.wav       replacement speech: lead/tail silence trimmed, loudnorm -16 LUFS, 44.1 kHz
  unrelated/nosrc_NN.mp4  no-source clips (none were recorded: the generated DEV clips stand in, see NOSRC)
  timing.json           per clip: Part 2 start and Part 3 start from Whisper word timestamps
  clips/*.mp4 + labels.csv  _reupload _lowq _cropped _banner _trimmed _words _words_lowq, and nosrc_NN
Then checks every _words clip (transcript window and unchanged picture) and prints an ffprobe table.
Only ffmpeg/ffprobe and the app's own Whisper (comparators/video.transcribe) run.
"""

import csv
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.comparators import video  # noqa: E402

MEDIA = ROOT / "data" / "media"
OFFICIAL, ALT, UNRELATED, CLIPS = (MEDIA / d for d in ("official", "alt", "unrelated", "clips"))
TRIM_S = 5  # the _trimmed clip starts this far into the source
# First words of Part 2 and of Part 3, as Whisper small writes them in each recording (garbled Hindi included;
# s08's Part 3 is taken from "इसे अपने", so its "हिम्मत रखें" line counts as Part 2).
# A capture group marks the anchor word when the phrase starts earlier. Checked by hand against the transcripts.
# A number is a time set by hand (s04: the word after "नहीं?" in a transcript of the original recording).
ANCHORS = {
    "s01": (r"every registered", r"thank you"),
    "s02": (r"\S+ पंजि", r"देख"),
    "s03": (r"a registered \S+ broker", r"this is all"),
    "s04": (15.1, r"इसके लिए"),  # Whisper writes 11.8-26 s as one junk token: start set by hand (see below)
    "s05": (r"real shares", r"thank you"),
    "s06": (r"(अस्ली|असली)", r"(दन्या|धन्य)"),
    "s07": (r"government bonds", r"thank you"),
    "s08": (r"तुरन्त राष्ट्", r"इसे अपने"),
}
# no source clips were recorded; these DEV clips (generated slides, synthetic voice) are never in the new index
NOSRC = ["unindexed/dev_new_1.mp4", "unindexed/dev_new_2.mp4", "unindexed/dev_new_3.mp4"] + [
    f"dev_official/dev_0{n}.mp4" for n in (1, 2, 3)
]
VARIANTS = {  # type -> ffmpeg output args (video re-encoded, audio kept)
    "reupload": ["-c:v", "libx264", "-crf", "28"],
    "lowq": ["-vf", "scale=-2:360", "-c:v", "libx264", "-crf", "36", "-b:a", "48k"],
    "cropped": ["-vf", "crop=iw*0.9:ih*0.9,scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-crf", "23"],
    "banner": ["-vf", "drawbox=y=ih*0.8:w=iw:h=ih*0.2:color=red@0.85:t=fill", "-c:v", "libx264", "-crf", "23"],
}


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *map(str, args)], check=True)


def probe(path: Path) -> dict:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type", "-of", "json", str(path)]
    j = json.loads(subprocess.run(cmd, capture_output=True, check=True, text=True).stdout)
    kinds = {s["codec_type"] for s in j["streams"]}
    return {"duration": float(j["format"]["duration"]), "audio": "audio" in kinds, "video": "video" in kinds}


def sid(path: Path) -> str:
    m = re.search(r"s0?([1-8])\b", path.stem.lower())
    return f"s0{m.group(1)}" if m else ""


def normalise_sources(folder: Path) -> None:
    OFFICIAL.mkdir(parents=True, exist_ok=True)
    for f in sorted(folder.iterdir()):
        if f.is_file() and sid(f):  # rotation is applied by ffmpeg's autorotate
            vf = "scale=w='min(1280,iw)':h='min(1280,ih)':force_original_aspect_ratio=decrease:force_divisible_by=2"
            ffmpeg(
                "-i", f, "-vf", f"{vf},fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "18",
                "-c:a", "aac", "-ar", "44100", "-b:a", "160k", "-movflags", "+faststart", OFFICIAL / f"{sid(f)}.mp4",
            )  # fmt: skip


def normalise_alts(folder: Path) -> None:
    ALT.mkdir(parents=True, exist_ok=True)
    trim = "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.1"  # leading only; reversed for tail
    for f in sorted(folder.iterdir()):
        if f.is_file() and sid(f):
            af = f"{trim},areverse,{trim},areverse,loudnorm=I=-16:TP=-1.5:LRA=11"
            ffmpeg("-i", f, "-vn", "-af", af, "-ar", "44100", ALT / f"{sid(f)}_alt.wav")


def norm_words(words: list[dict]) -> list[str]:
    return [re.sub(r"[,.?!।'\"]+", "", w["w"]).lower() for w in words]


def find(words: list[dict], pattern: str, after_s: float) -> int:
    """Index of the first word at or after after_s where pattern matches (its group 1 when it has one)."""
    toks = norm_words(words)
    for i in range(len(toks)):
        if words[i]["start"] < after_s:
            continue
        m = re.match(pattern, " ".join(toks[i:]))
        if m:
            return i + (len(m.string[: m.start(1)].split()) if m.groups() else 0)
    raise SystemExit(f"anchor {pattern!r} not found after {after_s} s; check the transcript")


def timing() -> dict:
    out = {}
    for f in sorted(OFFICIAL.glob("s0*.mp4")):
        s = f.stem
        words, lang = video.transcribe(f)
        p2, p3 = ANCHORS[s]
        start = p2 if isinstance(p2, float) else words[find(words, p2, 7.0)]["start"]
        j = find(words, p3, start + 1)
        alt = probe(ALT / f"{s}_alt.wav")["duration"] if (ALT / f"{s}_alt.wav").exists() else None
        out[s] = {
            "lang": lang,
            "start_s": start,
            "end_s": round(words[j]["start"] - 0.1, 2),  # up to Part 3: a transcript gap cannot cut Part 2 short
            "part3_s": words[j]["start"],
            "anchors": ["set by hand" if isinstance(p2, float) else p2, words[j]["w"]],
            "source_s": round(probe(f)["duration"], 2),
            "alt_s": round(alt, 2) if alt else None,
        }
    (MEDIA / "timing.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return out


def words_clip(src: Path, alt: Path, t: dict, out: Path) -> tuple[float, float, str]:
    """Original picture and audio; original muted over the replaced span; alt speech mixed in. Returns the span."""
    part2 = t["end_s"] - t["start_s"]
    tempo = min(1.15, t["alt_s"] / part2) if t["alt_s"] - part2 > 3 else 1.0  # never cut words; speed up a little
    alt_len = t["alt_s"] / tempo
    mute_to = max(t["end_s"], t["start_s"] + alt_len)
    ms = int(t["start_s"] * 1000)
    fc = (
        f"[0:a]volume=0:enable='between(t,{t['start_s']},{mute_to:.2f})'[a0];"
        f"[1:a]aresample=44100,atempo={tempo:.3f},adelay={ms}:all=1[a1];"
        "[a0][a1]amix=inputs=2:normalize=0:duration=first[a]"
    )
    ffmpeg("-i", src, "-i", alt, "-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "copy",
           "-c:a", "aac", "-ar", "44100", "-b:a", "160k", out)  # fmt: skip
    note = f"atempo {tempo:.3f}" if tempo > 1 else ""
    if mute_to > t["end_s"] + 0.05:
        note = (note + "; " if note else "") + f"alt runs {mute_to - t['end_s']:.1f} s into Part 3 (muted)"
    return round(t["start_s"], 2), round(t["start_s"] + alt_len, 2), note


def build(times: dict) -> list[dict]:
    CLIPS.mkdir(parents=True, exist_ok=True)
    UNRELATED.mkdir(parents=True, exist_ok=True)
    rows = []
    for s, t in times.items():
        src = OFFICIAL / f"{s}.mp4"
        base = {"source": src.name, "expect_source_found": 1, "expect_words_changed": 0}
        for kind, args in VARIANTS.items():
            ffmpeg("-i", src, *args, "-c:a", "aac", CLIPS / f"{s}_{kind}.mp4")
            rows.append({"file": f"{s}_{kind}.mp4", "type": kind, **base})
        ffmpeg("-ss", TRIM_S, "-i", src, "-c:v", "libx264", "-crf", "23", "-c:a", "aac", CLIPS / f"{s}_trimmed.mp4")
        rows.append({"file": f"{s}_trimmed.mp4", "type": "trimmed", **base})
        if not t["alt_s"]:
            print(f"{s}: no altered audio, no _words clips")
            continue
        a, b, note = words_clip(src, ALT / f"{s}_alt.wav", t, CLIPS / f"{s}_words.mp4")
        ffmpeg("-i", CLIPS / f"{s}_words.mp4", *VARIANTS["lowq"], "-c:a", "aac", CLIPS / f"{s}_words_lowq.mp4")
        changed = {"expect_words_changed": 1, "changed_from_s": a, "changed_to_s": b, "note": note}
        rows += [{"file": f"{s}_{k}.mp4", "type": k, **base, **changed} for k in ("words", "words_lowq")]
    for n, rel in enumerate(NOSRC, 1):
        name = f"nosrc_{n:02d}.mp4"
        ffmpeg("-i", MEDIA / rel, "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "20",
               "-c:a", "aac", "-ar", "44100", UNRELATED / name)  # fmt: skip
        ffmpeg("-i", UNRELATED / name, "-c", "copy", CLIPS / name)
        rows.append(
            {"file": name, "source": "", "type": "no_source", "expect_source_found": 0, "expect_words_changed": 0}
        )
    cols = ["file", "source", "type", "expect_source_found", "expect_words_changed", "changed_from_s", "changed_to_s"]
    with (CLIPS / "labels.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return rows


def pcm(path: Path) -> np.ndarray:
    cmd = ["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", "16000", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32)


def same_audio(a: np.ndarray, b: np.ndarray, lo: float, hi: float) -> float:
    """Correlation of two waveforms between lo and hi seconds (1.0 = the same sound)."""
    x, y = a[int(lo * 16000) : int(hi * 16000)], b[int(lo * 16000) : int(hi * 16000)]
    n = min(len(x), len(y))
    return float(np.corrcoef(x[:n], y[:n])[0, 1]) if n > 16000 else 1.0


def sim(a: list[dict], b: list[dict]) -> float:
    return difflib.SequenceMatcher(None, "".join(norm_words(a)), "".join(norm_words(b)), autojunk=False).ratio()


def verify(times: dict, rows: list[dict]) -> bool:
    """Every _words clip: the window says the alt words (not Part 2), Parts 1 and 3 are the original sound (waveform
    correlation; Whisper small drops or loops some Hindi lines, so its Part 1/3 scores are shown but do not decide),
    and the picture is the same."""
    ok = True
    print("\nverify _words clips (similarity of character strings of the Whisper transcripts, 0..1)")
    for r in (r for r in rows if r["type"] == "words"):
        s, t = r["file"][:3], times[r["file"][:3]]
        a, b = r["changed_from_s"], r["changed_to_s"]
        src_w, _ = video.transcribe(OFFICIAL / f"{s}.mp4", t["lang"])
        q_w, _ = video.transcribe(CLIPS / r["file"], t["lang"])
        alt_w, _ = video.transcribe(ALT / f"{s}_alt.wav", t["lang"])

        def part(ws, lo, hi):
            return [w for w in ws if lo <= (w["start"] + w["end"]) / 2 < hi]

        window = part(q_w, a - 0.5, b + 0.5)
        to_alt, to_orig = sim(window, alt_w), sim(window, part(src_w, t["start_s"], t["end_s"]))
        p1 = sim(part(q_w, 0, a - 0.5), part(src_w, 0, t["start_s"]))
        p3 = sim(part(q_w, max(b, t["end_s"]) + 0.3, 1e9), part(src_w, max(b, t["end_s"]) + 0.3, 1e9))
        wq, ws = pcm(CLIPS / r["file"]), pcm(OFFICIAL / f"{s}.mp4")
        mute_to = max(b, t["end_s"])
        c1, c3 = same_audio(wq, ws, 0, a - 0.3), same_audio(wq, ws, mute_to + 0.3, 1e9)
        fq, fs = video.phashes(video.frames(CLIPS / r["file"])), video.phashes(video.frames(OFFICIAL / f"{s}.mp4"))
        picture = all(fq[i] == fs[i] for i in (1, len(fs) // 2, len(fs) - 2))
        good = to_alt > to_orig and to_alt >= 0.4 and min(c1, c3) >= 0.95 and picture
        ok &= good
        print(
            f"  {'PASS' if good else 'FAIL'} {r['file']:16} window~alt {to_alt:.2f} window~orig {to_orig:.2f} "
            f"| audio part1 {c1:.3f} part3 {c3:.3f} | whisper part1 {p1:.2f} part3 {p3:.2f} | "
            f"picture {'same' if picture else 'DIFFERENT'}"
        )
    return ok


def table(rows: list[dict]) -> None:
    print(f"\n{'file':22} {'type':11} {'dur s':>6} {'KB':>6} audio  changed")
    for r in rows:
        f = CLIPS / r["file"]
        p = probe(f)
        span = f"{r['changed_from_s']}-{r['changed_to_s']} s {r.get('note', '')}" if r.get("changed_from_s") else ""
        print(f"{r['file']:22} {r['type']:11} {p['duration']:6.1f} {f.stat().st_size // 1024:6} "
              f"{'yes  ' if p['audio'] else 'NO   '}  {span}")  # fmt: skip
    assert all(probe(CLIPS / r["file"])["audio"] for r in rows), "a clip has no audio track"


if __name__ == "__main__":
    videos = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "IITD Videos"
    alts = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "IITD altered Audio"
    normalise_sources(videos)
    normalise_alts(alts)
    times = timing()
    print(f"{'id':4} {'lang':4} {'P2 start':>8} {'P2 end':>7} {'P3':>6} {'P2 s':>5} {'alt s':>6}  anchors")
    for s, t in times.items():
        print(f"{s:4} {t['lang']:4} {t['start_s']:8.2f} {t['end_s']:7.2f} {t['part3_s']:6.2f} "
              f"{t['end_s'] - t['start_s']:5.1f} {t['alt_s'] or 0:6.2f}  {t['anchors']}")  # fmt: skip
    missing = sorted({f"s0{n}" for n in range(1, 9)} - set(times))
    print(f"missing sources: {missing or 'none'}")
    rows = build(times)
    table(rows)
    sys.exit(0 if verify(times, rows) else 1)
