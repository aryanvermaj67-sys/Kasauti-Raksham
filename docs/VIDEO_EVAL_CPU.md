# Video evaluation: own test set made by the team, not independent

Run 25 Oct 2026 06:59, device cpu, 12 clips: `python scripts/video_eval.py data/media/clips/labels.csv`

## Summary

- reupload: source found top-1 1/1 (visual+audio_fingerprint 1)
- lowq: source found top-1 1/1 (audio_fingerprint 1)
- cropped: source found top-1 1/1 (visual+audio_fingerprint 1)
- banner: source found top-1 1/1 (audio_fingerprint 1)
- trimmed: source found top-1 1/1 (visual+audio_fingerprint 1)
- words: source found top-1 3/3 (visual+audio_fingerprint 3)
- words_lowq: source found top-1 3/3 (audio_fingerprint 3)
- source match over re-upload, low quality, cropped, banner, trimmed: 5/5
- words-changed clips: change found 6/6, reported span within 2 s of the real window 4/6, edge error median 1.7 s, worst 2.3 s
- no-source clips -> NO_RECORD: 1/1; MATCHES: 0
- false "changed words" on unchanged clips whose source was found: 0 
- seconds per clip: source search median 3.46, max 4.69; whole check (with transcript) median 12.78, max 48.04

## Per clip

| clip | type | source exp -> got | signal | changed exp -> got | span exp (s) | span got | verdict | reason |
|---|---|---|---|---|---|---|---|---|
| s02_words.mp4 | words | s02.mp4 -> s02.mp4 | visual + audio_fingerprint | 1 -> 1 | 13.8-30.4 | 0:13-0:30 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s02_words_lowq.mp4 | words_lowq | s02.mp4 -> s02.mp4 | audio_fingerprint | 1 -> 1 | 13.8-30.4 | 0:13-0:30 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s05_reupload.mp4 | reupload | s05.mp4 -> s05.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s05_lowq.mp4 | lowq | s05.mp4 -> s05.mp4 | audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s05_cropped.mp4 | cropped | s05.mp4 -> s05.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s05_banner.mp4 | banner | s05.mp4 -> s05.mp4 | audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s05_trimmed.mp4 | trimmed | s05.mp4 -> s05.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s05_words.mp4 | words | s05.mp4 -> s05.mp4 | visual + audio_fingerprint | 1 -> 1 | 11.8-24.9 | 0:11-0:26 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s05_words_lowq.mp4 | words_lowq | s05.mp4 -> s05.mp4 | audio_fingerprint | 1 -> 1 | 11.8-24.9 | 0:11-0:26 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s08_words.mp4 | words | s08.mp4 -> s08.mp4 | visual + audio_fingerprint | 1 -> 1 | 15.9-34.5 | 0:15-0:34, 0:35-0:36 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s08_words_lowq.mp4 | words_lowq | s08.mp4 -> s08.mp4 | audio_fingerprint | 1 -> 1 | 15.9-34.5 | 0:15-0:34, 0:35-0:36 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| nosrc_01.mp4 | no_source | - -> - | - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
