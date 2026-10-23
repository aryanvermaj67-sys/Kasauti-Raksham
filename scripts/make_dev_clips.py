"""Make DEV video clips for the source check until the consented clips exist. No real face or voice anywhere.

Usage: python scripts/make_dev_clips.py
Writes (git-ignored) data/media/:
  official/dev_NN.mp4      6 "official" clips: 45 one-second slides of generated shapes, DEV label, and the
                           built-in Windows synthetic voice (System.Speech) reading a ~100-word script
  fakes/dev_NN_fake*.mp4   the same frames from second 5 on, re-voiced with one sentence changed, plus
                           CRF 32, 10% crop and 480p variants; and a CRF 30 re-encode of each original (unchanged)
  unindexed/dev_new_N.mp4  3 clips made the same way but never indexed (must come out "no source found")
  dev_manifest.json        ground truth: expected source, offset and changed sentence per clip
"""

import json
import random
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
MEDIA = ROOT / "data" / "media"
SECONDS, OFFSET = 45, 5
FONT = ImageFont.truetype("arial.ttf", 34)
SMALL = ImageFont.truetype("arial.ttf", 20)
TOPICS = [
    ("Savings basics", "monthly savings", "build an emergency fund first", "move all your savings into one tip"),
    ("Market risk", "share prices", "prices can fall as well as rise", "prices only rise in this special group"),
    (
        "Checking a broker",
        "registered brokers",
        "check the registration number on SEBI Check",
        "skip the registration check to save time",
    ),
    (
        "Payments",
        "UPI payments",
        "pay only through the handle shown on your broker's own app",
        "pay the agent's personal account directly",
    ),
    (
        "Your demat account",
        "your holdings",
        "read your monthly statement from the depository",
        "trust the screenshot the group admin sends you",
    ),
    ("Tips and groups", "chat groups", "never act on a tip from a stranger", "always act fast on tips from this group"),
    ("New clip one", "loan offers", "read every term before you sign", "sign today before the offer closes"),
    ("New clip two", "insurance", "compare plans from licensed insurers", "buy the plan the caller recommends"),
    ("New clip three", "retirement", "start early and keep it simple", "move your pension into crypto now"),
]


def script(subject, line):
    return (
        f"This is a development clip about {subject}. It was made for testing and does not show a real person. "
        f"Good habits matter more than quick gains. Before you invest, write down what you want and when you need it. "
        f"Our main point today is simple: {line}. "
        f"Keep records of every payment you make, and keep the receipts in one place. "
        f"If someone pushes you to decide quickly, slow down and ask a person you trust. "
        f"Thank you for watching this short development clip about {subject}."
    )


def frame(path, clip, second, title):
    rng = random.Random(f"{clip}-{second}")
    img = Image.new("RGB", (1280, 720), tuple(rng.randrange(150, 256) for _ in range(3)))
    d = ImageDraw.Draw(img)
    for _ in range(12):
        x, y, r = rng.randrange(1280), rng.randrange(80, 720), rng.randrange(30, 160)
        box, colour = [x - r, y - r, x + r, y + r], tuple(rng.randrange(0, 200) for _ in range(3))
        (d.ellipse if rng.random() < 0.5 else d.rectangle)(box, fill=colour)
    d.rectangle([0, 0, 1280, 64], fill=(20, 20, 20))
    d.text((24, 12), f"{title} - slide {second + 1}", font=FONT, fill="white")
    d.text((1000, 680), "DEV CLIP - synthetic", font=SMALL, fill=(255, 255, 0), stroke_width=2, stroke_fill="black")
    img.save(path)


def speak(text, wav):
    """Windows built-in synthetic TTS voice; offline, not a real person's voice."""
    txt = wav.with_suffix(".txt")
    txt.write_text(text, encoding="utf-8")
    ps = (
        "Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f"$s.SelectVoice('Microsoft David Desktop'); $s.Rate = 0; $s.SetOutputToWaveFile('{wav}'); "
        f"$s.Speak([IO.File]::ReadAllText('{txt}')); $s.Dispose()"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def clip(frames_dir, wav, out, start=0):
    """1 fps slides + narration -> 25 fps H.264 mp4, from `start` seconds of the slide timeline."""
    ffmpeg(
        "-framerate", "1", "-start_number", str(start), "-i", str(frames_dir / "f%03d.png"),
        "-i", str(wav), "-t", str(SECONDS - start), "-r", "25", "-pix_fmt", "yuv420p",
        "-c:v", "libx264", "-crf", "20", "-c:a", "aac", "-af", "apad", str(out),
    )  # fmt: skip


def main():
    for d in ("official", "fakes", "unindexed"):
        (MEDIA / d).mkdir(parents=True, exist_ok=True)
    manifest = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for n, (title, subject, line, changed) in enumerate(TOPICS, 1):
            fdir = tmp / f"frames{n}"
            fdir.mkdir()
            for s in range(SECONDS):
                frame(fdir / f"f{s:03d}.png", n, s, title)
            speak(script(subject, line), tmp / f"real{n}.wav")
            if n > 6:  # never indexed: a clip with no source
                out = MEDIA / "unindexed" / f"dev_new_{n - 6}.mp4"
                clip(fdir, tmp / f"real{n}.wav", out)
                manifest.append({"file": str(out.relative_to(ROOT)), "source": None, "kind": "unindexed"})
                continue
            official = MEDIA / "official" / f"dev_{n:02d}.mp4"
            clip(fdir, tmp / f"real{n}.wav", official)
            src = str(official.relative_to(ROOT))
            reencode = MEDIA / "fakes" / f"dev_{n:02d}_reencode.mp4"
            ffmpeg("-i", str(official), "-c:v", "libx264", "-crf", "30", "-c:a", "aac", str(reencode))
            manifest.append(
                {
                    "file": str(reencode.relative_to(ROOT)),
                    "source": src,
                    "offset": 0,
                    "kind": "reencode",
                    "changed": None,
                }
            )
            # the fake: same slides from second OFFSET, re-voiced with one sentence changed; audio cut to match
            speak(script(subject, changed), tmp / f"fake{n}.wav")
            cut = tmp / f"fake{n}_cut.wav"
            ffmpeg("-ss", str(OFFSET), "-i", str(tmp / f"fake{n}.wav"), str(cut))
            fake = MEDIA / "fakes" / f"dev_{n:02d}_fake.mp4"
            clip(fdir, cut, fake, start=OFFSET)
            variants = {
                "fake": None,
                "fake_crf32": ["-c:v", "libx264", "-crf", "32"],
                "fake_crop10": ["-vf", "crop=iw*0.9:ih*0.9", "-c:v", "libx264", "-crf", "23"],
                "fake_480p": ["-vf", "scale=-2:480", "-c:v", "libx264", "-crf", "23"],
            }
            for kind, args in variants.items():
                out = MEDIA / "fakes" / f"dev_{n:02d}_{kind}.mp4"
                if args:
                    ffmpeg("-i", str(fake), *args, "-c:a", "aac", str(out))
                manifest.append(
                    {
                        "file": str(out.relative_to(ROOT)),
                        "source": src,
                        "offset": OFFSET,
                        "kind": kind,
                        "changed": [line, changed],
                    }
                )
    (MEDIA / "dev_manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    for d in ("official", "fakes", "unindexed"):
        files = sorted((MEDIA / d).glob("*.mp4"))
        print(f"{d}: {len(files)} clips")


if __name__ == "__main__":
    main()
