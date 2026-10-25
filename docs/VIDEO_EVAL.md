# Video evaluation: own test set made by the team, not independent

Run 25 Oct 2026 08:41, device cuda, 62 clips: `python scripts/video_eval.py data/media/clips/labels.csv`

## Summary

- reupload: source found top-1 8/8 (visual+audio_fingerprint 8)
- lowq: source found top-1 8/8 (audio_fingerprint 8)
- cropped: source found top-1 8/8 (audio_fingerprint 1, visual+audio_fingerprint 7)
- banner: source found top-1 8/8 (audio_fingerprint 8)
- trimmed: source found top-1 8/8 (visual+audio_fingerprint 8)
- words: source found top-1 8/8 (visual+audio_fingerprint 8)
- words_lowq: source found top-1 8/8 (audio_fingerprint 8)
- source match over re-upload, low quality, cropped, banner, trimmed: 40/40
- words-changed clips: change found 16/16, reported span within 2 s of the real window 14/16, edge error median 0.6 s, worst 2.3 s
- no-source clips -> NO_RECORD: 6/6; MATCHES: 0
- false "changed words" on unchanged clips whose source was found: 0 
- seconds per clip: source search median 1.14, max 2.12; whole check (with transcript) median 3.69, max 15.04

## Per clip

| clip | type | source exp -> got | signal | changed exp -> got | span exp (s) | span got | verdict | reason |
|---|---|---|---|---|---|---|---|---|
| s01_reupload.mp4 | reupload | s01.mp4 -> s01.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s01_lowq.mp4 | lowq | s01.mp4 -> s01.mp4 | audio_fingerprint | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_SOUND_ONLY_SAME |
| s01_cropped.mp4 | cropped | s01.mp4 -> s01.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s01_banner.mp4 | banner | s01.mp4 -> s01.mp4 | audio_fingerprint | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_SOUND_ONLY_SAME |
| s01_trimmed.mp4 | trimmed | s01.mp4 -> s01.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s01_words.mp4 | words | s01.mp4 -> s01.mp4 | visual + audio_fingerprint | 1 -> 1 | 13.6-31.8 | 0:13-0:31 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s01_words_lowq.mp4 | words_lowq | s01.mp4 -> s01.mp4 | audio_fingerprint | 1 -> 1 | 13.6-31.8 | 0:13-0:31 | CONTRADICTS | ENDORSEMENT_SOUND_ONLY_CHANGED |
| s02_reupload.mp4 | reupload | s02.mp4 -> s02.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s02_lowq.mp4 | lowq | s02.mp4 -> s02.mp4 | audio_fingerprint | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_SOUND_ONLY_SAME |
| s02_cropped.mp4 | cropped | s02.mp4 -> s02.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s02_banner.mp4 | banner | s02.mp4 -> s02.mp4 | audio_fingerprint | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_SOUND_ONLY_SAME |
| s02_trimmed.mp4 | trimmed | s02.mp4 -> s02.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s02_words.mp4 | words | s02.mp4 -> s02.mp4 | visual + audio_fingerprint | 1 -> 1 | 13.8-30.4 | 0:13-0:30 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s02_words_lowq.mp4 | words_lowq | s02.mp4 -> s02.mp4 | audio_fingerprint | 1 -> 1 | 13.8-30.4 | 0:13-0:30 | CONTRADICTS | ENDORSEMENT_SOUND_ONLY_CHANGED |
| s03_reupload.mp4 | reupload | s03.mp4 -> s03.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s03_lowq.mp4 | lowq | s03.mp4 -> s03.mp4 | audio_fingerprint | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_SOUND_ONLY_SAME |
| s03_cropped.mp4 | cropped | s03.mp4 -> s03.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s03_banner.mp4 | banner | s03.mp4 -> s03.mp4 | audio_fingerprint | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_SOUND_ONLY_SAME |
| s03_trimmed.mp4 | trimmed | s03.mp4 -> s03.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s03_words.mp4 | words | s03.mp4 -> s03.mp4 | visual + audio_fingerprint | 1 -> 1 | 14.2-30.2 | 0:14-0:30 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s03_words_lowq.mp4 | words_lowq | s03.mp4 -> s03.mp4 | audio_fingerprint | 1 -> 1 | 14.2-30.2 | 0:14-0:30 | CONTRADICTS | ENDORSEMENT_SOUND_ONLY_CHANGED |
| s04_reupload.mp4 | reupload | s04.mp4 -> s04.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s04_lowq.mp4 | lowq | s04.mp4 -> s04.mp4 | audio_fingerprint | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_SOUND_ONLY_SAME |
| s04_cropped.mp4 | cropped | s04.mp4 -> s04.mp4 | audio_fingerprint | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_SOUND_ONLY_SAME |
| s04_banner.mp4 | banner | s04.mp4 -> s04.mp4 | audio_fingerprint | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_SOUND_ONLY_SAME |
| s04_trimmed.mp4 | trimmed | s04.mp4 -> s04.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s04_words.mp4 | words | s04.mp4 -> s04.mp4 | visual + audio_fingerprint | 1 -> 1 | 15.1-30.8 | 0:15-0:31 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s04_words_lowq.mp4 | words_lowq | s04.mp4 -> s04.mp4 | audio_fingerprint | 1 -> 1 | 15.1-30.8 | 0:15-0:31 | CONTRADICTS | ENDORSEMENT_SOUND_ONLY_CHANGED |
| s05_reupload.mp4 | reupload | s05.mp4 -> s05.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s05_lowq.mp4 | lowq | s05.mp4 -> s05.mp4 | audio_fingerprint | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_SOUND_ONLY_SAME |
| s05_cropped.mp4 | cropped | s05.mp4 -> s05.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s05_banner.mp4 | banner | s05.mp4 -> s05.mp4 | audio_fingerprint | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_SOUND_ONLY_SAME |
| s05_trimmed.mp4 | trimmed | s05.mp4 -> s05.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s05_words.mp4 | words | s05.mp4 -> s05.mp4 | visual + audio_fingerprint | 1 -> 1 | 11.8-24.9 | 0:11-0:26 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s05_words_lowq.mp4 | words_lowq | s05.mp4 -> s05.mp4 | audio_fingerprint | 1 -> 1 | 11.8-24.9 | 0:11-0:26 | CONTRADICTS | ENDORSEMENT_SOUND_ONLY_CHANGED |
| s06_reupload.mp4 | reupload | s06.mp4 -> s06.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s06_lowq.mp4 | lowq | s06.mp4 -> s06.mp4 | audio_fingerprint | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_SOUND_ONLY_SAME |
| s06_cropped.mp4 | cropped | s06.mp4 -> s06.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s06_banner.mp4 | banner | s06.mp4 -> s06.mp4 | audio_fingerprint | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_SOUND_ONLY_SAME |
| s06_trimmed.mp4 | trimmed | s06.mp4 -> s06.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s06_words.mp4 | words | s06.mp4 -> s06.mp4 | visual + audio_fingerprint | 1 -> 1 | 16.4-34.7 | 0:16-0:36 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s06_words_lowq.mp4 | words_lowq | s06.mp4 -> s06.mp4 | audio_fingerprint | 1 -> 1 | 16.4-34.7 | 0:16-0:36 | CONTRADICTS | ENDORSEMENT_SOUND_ONLY_CHANGED |
| s07_reupload.mp4 | reupload | s07.mp4 -> s07.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s07_lowq.mp4 | lowq | s07.mp4 -> s07.mp4 | audio_fingerprint | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_SOUND_ONLY_SAME |
| s07_cropped.mp4 | cropped | s07.mp4 -> s07.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s07_banner.mp4 | banner | s07.mp4 -> s07.mp4 | audio_fingerprint | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_SOUND_ONLY_SAME |
| s07_trimmed.mp4 | trimmed | s07.mp4 -> s07.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s07_words.mp4 | words | s07.mp4 -> s07.mp4 | visual + audio_fingerprint | 1 -> 1 | 14.3-34.3 | 0:14-0:34 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s07_words_lowq.mp4 | words_lowq | s07.mp4 -> s07.mp4 | audio_fingerprint | 1 -> 1 | 14.3-34.3 | 0:14-0:34 | CONTRADICTS | ENDORSEMENT_SOUND_ONLY_CHANGED |
| s08_reupload.mp4 | reupload | s08.mp4 -> s08.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s08_lowq.mp4 | lowq | s08.mp4 -> s08.mp4 | audio_fingerprint | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_SOUND_ONLY_SAME |
| s08_cropped.mp4 | cropped | s08.mp4 -> s08.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s08_banner.mp4 | banner | s08.mp4 -> s08.mp4 | audio_fingerprint | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_SOUND_ONLY_SAME |
| s08_trimmed.mp4 | trimmed | s08.mp4 -> s08.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s08_words.mp4 | words | s08.mp4 -> s08.mp4 | visual + audio_fingerprint | 1 -> 1 | 15.9-34.5 | 0:15-0:34, 0:35-0:36 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s08_words_lowq.mp4 | words_lowq | s08.mp4 -> s08.mp4 | audio_fingerprint | 1 -> 1 | 15.9-34.5 | 0:15-0:34, 0:35-0:36 | CONTRADICTS | ENDORSEMENT_SOUND_ONLY_CHANGED |
| nosrc_01.mp4 | no_source | - -> - | - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| nosrc_02.mp4 | no_source | - -> - | - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| nosrc_03.mp4 | no_source | - -> - | - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| nosrc_04.mp4 | no_source | - -> - | - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| nosrc_05.mp4 | no_source | - -> - | - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| nosrc_06.mp4 | no_source | - -> - | - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
