# Demo day runbook

One laptop (the GPU one), Wi-Fi off. Each step lists what you should see. If a step fails, use the fixes at the end.

## 1. Close first

Games, video players, other model servers, extra browser windows (each takes GPU memory), and OneDrive/Windows Update (disk and network). Keep one browser window for the demo.

## 2. Reset (every time before going on stage)

The backend must be stopped first.

```powershell
cd "D:\Kasauti IITD"
scripts\reset_demo.ps1
```

You should see `reset OK`, evidence checks 0, reviewer queue 0, registry seed entries 79 (MOCK). The script writes an `EVIDENCE_KEY` to `.env` if there is none.

## 3. Start, in this order

1. **Ollama**: Start menu > Ollama (only for `local` mode; the stage demo uses `cache` and does not need it).
2. **Backend** (new PowerShell window):
   ```powershell
   cd "D:\Kasauti IITD\backend"
   Get-Content ..\.env | Where-Object { $_ -match '^\w+=' } | ForEach-Object { $k, $v = $_ -split '=', 2; Set-Item "env:$k" $v }
   $env:LLM_PROVIDER = "cache"; $env:HF_HUB_OFFLINE = "1"
   python -m uvicorn app.main:app --port 8000
   ```
3. **Frontend** (another window): `cd "D:\Kasauti IITD\frontend"; npm run dev`
4. Open `http://localhost:5173/present` (phone and reviewer console side by side; set `$env:KASAUTI_DEMO = "1"` before starting the backend so Run and Reset work), or `/app` and `/reviewer` in two windows. The phone at `/app?customer=SYN-C0001` It shows "Preparing the checker" with **Check** disabled until the models are loaded.

**How long to wait.** Measured on the demo laptop: `video models ready` in the backend window after 29–41 s in `cache` mode; `/health` ready after 47–48 s in `local` mode (Ollama model and EasyOCR too). The Check button turns on by itself.

## 4. Preflight

```powershell
scripts\preflight.ps1
```

It must print `GO`. A `NO-GO` lists exactly what to fix. GPU rule: 4 GB free before start, 1.6 GB free once the models are loaded.

Full rehearsal in one command (resets, starts both, runs every flow, stops): `scripts\demo.ps1`. It must end with `demo OK offline`. Run it, then reset again before the real demo.

## 5. If something fails

| Problem | Sign | Fix |
|---|---|---|
| GPU out of memory | `CUDA out of memory` in the backend window, or preflight GPU `NO` | Close GPU apps. In `local` mode, stop the backend, add `$env:KASAUTI_LOCAL_MODEL = "qwen2.5:3b"` (smaller model), start again. Last resort: `$env:CUDA_VISIBLE_DEVICES = "-1"` (CPU; video 18 s, a `local` screenshot read 40–45 s) |
| Ollama down | preflight `Ollama models NO`; backend prints `local reader failed, using offline reader` | Nothing to do for a single read: it falls back to the offline reader by itself. To stop trying Ollama: `$env:LLM_PROVIDER = "offline"` and restart the backend (Tesseract with the Hindi pack) |
| Network dies | nothing visible | The stage demo needs none: use `$env:LLM_PROVIDER = "cache"` (replays the stored reading of the demo screenshots only; rules, records and evidence still run live) |
| A screenshot not in the cache | `no cached ClaimSet` error | Switch to `local` (or `offline`) and restart the backend |
| Demo flow breaks on stage | | Play the recorded backup video of the run |
| Old checks in the reviewer queue | queue not empty, preflight `evidence DB NO` | Stop the backend, `scripts\reset_demo.ps1`, start again |

## 6. Wi-Fi-off checklist (do it once fully, the evening before)

- [ ] Wi-Fi off, Ethernet out, mobile hotspot off (Windows tray shows no network)
- [ ] `scripts\reset_demo.ps1` prints `reset OK`
- [ ] Ollama running; backend and frontend started as in step 3
- [ ] `scripts\preflight.ps1` prints `GO` (git tree clean, commit hash noted)
- [ ] demo-001 in English and Hindi, demo-002, demo-003, the video clip `demo_media\s05_words.mp4` and the reviewer approval each clicked through by hand (script: `docs/DEMO.md`)
- [ ] Hindi text renders (Noto Sans Devanagari is bundled; no font download)
- [ ] One `local` read of a new screenshot works, to prove the fallback path
- [ ] Reset again; leave the laptop on charge with the backend running

## 7. Video clips (the team's consented recordings)

Originals stay untouched in `IITD Videos\` (S01-S08) and `IITD altered Audio\` (the re-voiced Part 2 lines); both are git-ignored. Everything below is made from them and is git-ignored too (people's faces and voices are never committed).

| Path | What |
|---|---|
| `data\media\official\s01-s08.mp4` | sources, H.264/AAC 44.1 kHz, 30 fps. The only files in the footage index (MOCK official archive) |
| `data\media\alt\s0N_alt.wav` | altered speech, silence trimmed, loudness -16 LUFS |
| `data\media\timing.json` | per clip: where Part 2 starts and Part 3 begins (Whisper word times; s04's start set by hand) |
| `data\media\clips\` + `labels.csv` | `_reupload _lowq _cropped _banner _trimmed _words _words_lowq` per source, and `nosrc_01-06` |
| `data\media\unrelated\nosrc_NN.mp4` | no-source clips: no unrelated clips were recorded, so the generated DEV clips stand in |
| `data\media\dev_official\`, `data\footage_index_dev\` | the old DEV clips and their index (used only by `backend\tests\test_video.py`) |
| `demo_media\` | `s05.mp4`, `s05_words.mp4`, `s05_words_lowq.mp4` for the stage demo |

Rebuild everything (about 4 min on the GPU), then the index and the evaluation:

```powershell
python scripts\make_test_clips.py "IITD Videos" "IITD altered Audio"
python scripts\build_footage_index.py data\media\official
python scripts\video_eval.py data\media\clips\labels.csv --out docs\VIDEO_EVAL
```

The index holds the audio fingerprints and log-mel frames (`data\footage_index\audio.npz`); an index built before 25 Oct lacks it, the backend then answers 503 "footage index not built" and preflight shows `model weights NO`: run `python scripts\build_footage_index.py data\media\official` once (about 75 s). The audio thresholds come from `python scripts\calibrate_audio.py` (source clips only; numbers in progress.md).

Demo clip: upload `demo_media\s05_words.mp4` with demo-001 (Present > Run does this). Expected: source `s05.mp4` found (picture and sound), words changed at `0:11-0:26`, CONTRADICTS. Measured 25 Oct on the GPU: 9.4 s from upload to result (source search 1.2 s). On CPU the whole video check is about 13 s for English clips and up to 48 s for Hindi ones.

Offline: `scripts\demo.ps1` runs the backend with a guard that refuses every non-local connection and must print `backend network attempts blocked by the offline guard: 0` and `demo OK offline`. To test with the radio really off: Wi-Fi off, then run the same command.

Tools and weights: ffmpeg 9.0.2 from winget (`%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_...\ffmpeg-9.0.2-full_build\bin`, on PATH). CLIP ViT-B/32 in `models\open_clip\`, faster-whisper small in `models\whisper\` (both read offline). The pen-drive kit (`scripts\make_kit.ps1`) copies `models\`, `data\media\` (official, clips, alt, unrelated, timing), `data\footage_index\`, `data\footage_index_dev\` and `demo_media\`; a second laptop also needs ffmpeg on PATH.
