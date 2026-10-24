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
4. Open `http://localhost:5173/app?customer=SYN-C0001`. It shows "Preparing the checker" with **Check** disabled until the models are loaded.

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
- [ ] demo-001 in English and Hindi, demo-002, demo-003, the fake clip and the reviewer approval each clicked through by hand (script: `docs/DEMO.md`)
- [ ] Hindi text renders (Noto Sans Devanagari is bundled; no font download)
- [ ] One `local` read of a new screenshot works, to prove the fallback path
- [ ] Reset again; leave the laptop on charge with the backend running
