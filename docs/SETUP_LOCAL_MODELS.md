# Free local model stack (claim reader)

The hackathon forbids paid APIs, so the claim reader's local option is free and runs offline once downloaded: EasyOCR (Hindi + English) reads the text, and a small Ollama model turns it into the fixed claim schema. Installed and checked on 24 Oct 2026 (Windows 11, RTX 5050 8 GB, Python 3.14.6, no venv). The reader that uses it is described below.

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

## The reader built on it (`LLM_PROVIDER=local`, the default)

`backend/app/reader/local.py`: EasyOCR (hi+en, GPU if available) -> text -> Ollama on localhost with the output format set to `claims.schema.json` (minus the fields code fills: sha256, claim ids, reader; no endorsement claims, those come from video) -> validated by the Pydantic `ClaimSet`. Invalid output gets one retry, then `ReaderError`, then `reader/__init__.py` answers with the offline (Tesseract) reader and sets `reader.fallback = true`, which the evidence chain records (`reader_fallback` in the `claims` entry of the pack). 60 s limit; only loopback calls (`OLLAMA_HOST` must be localhost). Only validated claims reach the router; code also drops claims that read like an instruction, nulls a SEBI registration number that is not in SEBI's format, nulls a total that disagrees with its own holding lines, and drops payees with no UPI id, account or IFSC. The backend warms the model at startup (the first call is 100+ s cold).

Models, scored on the three demo screenshots (56 fields; `scripts/eval_local_reader.py`, full per-field tables in `docs/LOCAL_READER_EVAL_GPU.md` and `docs/LOCAL_READER_EVAL_CPU.md`):

| | gemma3:4b (default) | qwen2.5:3b (fallback) |
|---|---|---|
| Fields right, GPU | 56/56 | 49/56 (missed a payee, misread an Indian-format total) |
| Fields right, CPU | 56/56 | 53/56 |
| Claims invented | 0 | 0 |
| Seconds per image, GPU (OCR + model) | 1.2 + 3.3 | 1.2 + 3.0 |
| Seconds per image, CPU (OCR + model) | 13 + 33 | 13 + 31 |
| VRAM | 7.1 GB peak with CLIP, Whisper small and EasyOCR also loaded (of 8.15 GB) | 4.3 GB alone |

The two `ex_s*` images in `data/frozen_example/` are tiny and EasyOCR garbles them ("Inicsys", "Faliance"); both models get under half their fields. Their labels are illustrations (they expect an ISIN the image does not show), so they are shown but not scored. Hindi screenshots read correctly except the ISIN O/0 confusion (`INEOO2A01018`); the customer corrects claims on the confirm screen. Small-sample caution: 3 images, one run per model on GPU; qwen scored 49/56 on GPU and 53/56 on CPU for the same images, so its output varies between runs. Set `KASAUTI_LOCAL_MODEL=qwen2.5:3b` to switch the default.

On demo-001..003 the verdicts through the real API on `LLM_PROVIDER=local` equal the verdicts from the regenerated cache and from the earlier offline-reader cache (`scripts/compare_reader_verdicts.py`).

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
