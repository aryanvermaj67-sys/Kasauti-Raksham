# Video evaluation: own test set made by the team, not independent

Run 25 Oct 2026 05:08, device cpu, 10 clips: `python scripts/video_eval.py data/media/clips/labels.csv`

## Summary

- reupload: source found top-1 1/1
- lowq: source found top-1 0/1
- cropped: source found top-1 1/1
- banner: source found top-1 0/1
- trimmed: source found top-1 1/1
- words: source found top-1 2/2
- words_lowq: source found top-1 0/2
- source match over re-upload, low quality, cropped, banner, trimmed: 3/5
- words-changed clips: change found 2/4, reported span within 2 s of the real window 1/4, edge error median 6.3 s, worst 11.8 s
- no-source clips -> NO_RECORD: 1/1; MATCHES: 0
- false "changed words" on unchanged clips whose source was found: 0 
- seconds per clip: source search median 3.40, max 4.06; whole check (with transcript) median 15.59, max 55.50

## Per clip

| clip | type | source exp -> got | changed exp -> got | span exp (s) | span got | verdict | reason |
|---|---|---|---|---|---|---|---|
| s02_words.mp4 | words | s02.mp4 -> s02.mp4 | 1 -> 1 | 13.8-30.4 | 0:02-0:03, 0:06-0:06, 0:11-0:35 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s02_words_lowq.mp4 | words_lowq | s02.mp4 -> - | 1 -> 0 | 13.8-30.4 |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s05_reupload.mp4 | reupload | s05.mp4 -> s05.mp4 | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s05_lowq.mp4 | lowq | s05.mp4 -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s05_cropped.mp4 | cropped | s05.mp4 -> s05.mp4 | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s05_banner.mp4 | banner | s05.mp4 -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s05_trimmed.mp4 | trimmed | s05.mp4 -> s05.mp4 | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s05_words.mp4 | words | s05.mp4 -> s05.mp4 | 1 -> 1 | 11.8-24.9 | 0:12-0:24 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s05_words_lowq.mp4 | words_lowq | s05.mp4 -> - | 1 -> 0 | 11.8-24.9 |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| nosrc_01.mp4 | no_source | - -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
