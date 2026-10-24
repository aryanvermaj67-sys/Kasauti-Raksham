# Free local model stack (claim reader)

The hackathon forbids paid APIs, so the claim reader's local option is free and runs offline once downloaded: EasyOCR (Hindi + English) reads the text, and a small Ollama model turns it into the fixed claim schema. Installed and checked on 24 Oct 2026 (Windows 11, RTX 5050 8 GB, Python 3.14.6, no venv). This is a smoke-tested stack, not the reader yet: `LLM_PROVIDER` has no local option, and `claims.schema.json` has no local provider value.

## What was installed

| Item | Version | Size | Where |
|---|---|---|---|
| Ollama (winget `Ollama.Ollama`) | 0.40.10 | 3.1 GB on disk (with GPU runtimes) | `%LOCALAPPDATA%\Programs\Ollama\` (not on PATH) |
| `qwen2.5:3b` | 357c53fb659c | 1.9 GB | `%USERPROFILE%\.ollama\models` |
| `gemma3:4b` | 68ceab7e468a | 3.4 GB | `%USERPROFILE%\.ollama\models` |
| EasyOCR | 1.7.2 | 285 MB of weights (`craft_mlt_25k.pth`, `devanagari.pth`) | `%USERPROFILE%\.EasyOCR\model` |
| python-bidi | 0.4.2 (pure Python) | tiny | project Python |

python-bidi 0.6.x ships a DLL that this laptop's Windows Application Control policy blocks (`DLL load failed while importing bidi`). 0.4.2 has no DLL but lacks the `bidi.get_display` name that easyocr imports, so any script that imports easyocr first runs `import bidi, bidi.algorithm; bidi.get_display = bidi.algorithm.get_display` (see `scripts/check_local_models.py`). It only matters for right-to-left scripts; Hindi and English do not use it.

On Windows, set `PYTHONUTF8=1` (or run `python -X utf8`): EasyOCR's download progress bar and Hindi output crash on the default cp1252 console.

## Smoke test results (qwen2.5:3b, structured output set to `docs/formats/claims.schema.json`)

| | demo-001.png (EN) | `docs/screens/confirm_hi.png` (HI) |
|---|---|---|
| EasyOCR (GPU, warm) | 1.7 s | 2.1 s |
| qwen2.5:3b, warm | 14.3 s | 9.6 s (first call after loading the model: 147 s) |
| Output validates against the schema | yes | yes |
| Peak VRAM, with CLIP + Whisper small + EasyOCR + qwen loaded | 5.5 GB of 8.15 GB | 4.9 GB of 8.15 GB |

Quality is not good enough yet; this is why the reader is not built:
- demo-001: every claim came back as `endorsement` and no `holding` or `broker` claim appeared; `portfolio_total_inr` was 5 instead of 39800000.
- Hindi sample: holdings, quantities and values were right, but EasyOCR read the ISINs with letter O for zero (`INEOO2A01018`), and the button text "आगे बढ़ें" became a second broker.
- The schema requires `artifact_sha256` and `reader`, which code should fill, not the model. A reader built on this should ask the model only for `claims` and `portfolio_total_inr`, with a smaller schema per claim type.

## Folders to copy for offline use

Copy these to the same relative place under the user profile on the other laptop:

1. `%USERPROFILE%\.ollama\models` (about 5 GB; contains `blobs` and `manifests`).
2. `%USERPROFILE%\.EasyOCR\model` (285 MB).

Ollama's model folder can be moved with the `OLLAMA_MODELS` environment variable, and EasyOCR's with `EASYOCR_MODULE_PATH` (the `model` folder goes inside it).

## Repeat on another laptop

With internet, once:

```
winget install --id Ollama.Ollama -e --accept-package-agreements --accept-source-agreements
ollama pull qwen2.5:3b
ollama pull gemma3:4b
pip install -r backend/requirements-local.txt
python -X utf8 -c "import bidi, bidi.algorithm; bidi.get_display = bidi.algorithm.get_display; import easyocr; easyocr.Reader(['hi','en'], gpu=False, verbose=False)"
python -X utf8 scripts/check_local_models.py
```

The `easyocr.Reader` line downloads the two weight files. Without internet, copy the two folders above, install Ollama and the pip packages from `wheels/` (rebuild `wheels/` for that laptop's Python version), then run the last command; it must print `local models OK` and exit 0. If Ollama is not running it prints which check failed and exits 1; start it with `ollama serve`.
