# Video evaluation: own test set made by the team, not independent

Run 25 Oct 2026 05:22, device cuda, 62 clips: `python scripts/video_eval.py data/media/clips/labels.csv`

## Summary

- reupload: source found top-1 8/8
- lowq: source found top-1 0/8
- cropped: source found top-1 7/8
- banner: source found top-1 0/8
- trimmed: source found top-1 8/8
- words: source found top-1 8/8
- words_lowq: source found top-1 0/8
- source match over re-upload, low quality, cropped, banner, trimmed: 23/40
- words-changed clips: change found 8/16, reported span within 2 s of the real window 3/16, edge error median 5.7 s, worst 15.4 s
- no-source clips -> NO_RECORD: 6/6; MATCHES: 0
- false "changed words" on unchanged clips whose source was found: 17 ['s01_trimmed.mp4', 's02_reupload.mp4', 's02_cropped.mp4', 's02_trimmed.mp4', 's03_reupload.mp4', 's03_cropped.mp4', 's03_trimmed.mp4', 's04_reupload.mp4', 's04_trimmed.mp4', 's05_reupload.mp4', 's05_cropped.mp4', 's06_reupload.mp4', 's06_cropped.mp4', 's06_trimmed.mp4', 's08_reupload.mp4', 's08_cropped.mp4', 's08_trimmed.mp4']
- seconds per clip: source search median 0.79, max 1.44; whole check (with transcript) median 3.79, max 14.05

## Per clip

| clip | type | source exp -> got | changed exp -> got | span exp (s) | span got | verdict | reason |
|---|---|---|---|---|---|---|---|
| s01_reupload.mp4 | reupload | s01.mp4 -> s01.mp4 | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s01_lowq.mp4 | lowq | s01.mp4 -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s01_cropped.mp4 | cropped | s01.mp4 -> s01.mp4 | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s01_banner.mp4 | banner | s01.mp4 -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s01_trimmed.mp4 | trimmed | s01.mp4 -> s01.mp4 | 0 -> 1 |  | 0:15-0:16 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s01_words.mp4 | words | s01.mp4 -> s01.mp4 | 1 -> 1 | 13.6-31.8 | 0:14-0:31, 0:36-0:36 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s01_words_lowq.mp4 | words_lowq | s01.mp4 -> - | 1 -> 0 | 13.6-31.8 |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s02_reupload.mp4 | reupload | s02.mp4 -> s02.mp4 | 0 -> 1 |  | 0:02-0:03, 0:12-0:12, 0:27-0:35 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s02_lowq.mp4 | lowq | s02.mp4 -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s02_cropped.mp4 | cropped | s02.mp4 -> s02.mp4 | 0 -> 1 |  | 0:02-0:03, 0:12-0:12, 0:27-0:35 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s02_banner.mp4 | banner | s02.mp4 -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s02_trimmed.mp4 | trimmed | s02.mp4 -> s02.mp4 | 0 -> 1 |  | 0:21-0:30 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s02_words.mp4 | words | s02.mp4 -> s02.mp4 | 1 -> 1 | 13.8-30.4 | 0:02-0:02, 0:06-0:06, 0:11-0:35 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s02_words_lowq.mp4 | words_lowq | s02.mp4 -> - | 1 -> 0 | 13.8-30.4 |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s03_reupload.mp4 | reupload | s03.mp4 -> s03.mp4 | 0 -> 1 |  | 0:08-0:09 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s03_lowq.mp4 | lowq | s03.mp4 -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s03_cropped.mp4 | cropped | s03.mp4 -> s03.mp4 | 0 -> 1 |  | 0:08-0:09 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s03_banner.mp4 | banner | s03.mp4 -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s03_trimmed.mp4 | trimmed | s03.mp4 -> s03.mp4 | 0 -> 1 |  | 0:04-0:04, 0:10-0:11 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s03_words.mp4 | words | s03.mp4 -> s03.mp4 | 1 -> 1 | 14.2-30.2 | 0:14-0:29 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s03_words_lowq.mp4 | words_lowq | s03.mp4 -> - | 1 -> 0 | 14.2-30.2 |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s04_reupload.mp4 | reupload | s04.mp4 -> s04.mp4 | 0 -> 1 |  | 0:07-0:40 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s04_lowq.mp4 | lowq | s04.mp4 -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s04_cropped.mp4 | cropped | s04.mp4 -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s04_banner.mp4 | banner | s04.mp4 -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s04_trimmed.mp4 | trimmed | s04.mp4 -> s04.mp4 | 0 -> 1 |  | 0:10-0:35 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s04_words.mp4 | words | s04.mp4 -> s04.mp4 | 1 -> 1 | 15.1-30.8 | 0:14-0:38 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s04_words_lowq.mp4 | words_lowq | s04.mp4 -> - | 1 -> 0 | 15.1-30.8 |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s05_reupload.mp4 | reupload | s05.mp4 -> s05.mp4 | 0 -> 1 |  | 0:13-0:13 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s05_lowq.mp4 | lowq | s05.mp4 -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s05_cropped.mp4 | cropped | s05.mp4 -> s05.mp4 | 0 -> 1 |  | 0:13-0:13 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s05_banner.mp4 | banner | s05.mp4 -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s05_trimmed.mp4 | trimmed | s05.mp4 -> s05.mp4 | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s05_words.mp4 | words | s05.mp4 -> s05.mp4 | 1 -> 1 | 11.8-24.9 | 0:12-0:24 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s05_words_lowq.mp4 | words_lowq | s05.mp4 -> - | 1 -> 0 | 11.8-24.9 |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s06_reupload.mp4 | reupload | s06.mp4 -> s06.mp4 | 0 -> 1 |  | 0:29-0:29, 0:32-0:32, 0:37-0:41 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s06_lowq.mp4 | lowq | s06.mp4 -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s06_cropped.mp4 | cropped | s06.mp4 -> s06.mp4 | 0 -> 1 |  | 0:29-0:29, 0:32-0:32, 0:37-0:41 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s06_banner.mp4 | banner | s06.mp4 -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s06_trimmed.mp4 | trimmed | s06.mp4 -> s06.mp4 | 0 -> 1 |  | 0:04-0:08, 0:11-0:21, 0:27-0:27, 0:31-0:36 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s06_words.mp4 | words | s06.mp4 -> s06.mp4 | 1 -> 1 | 16.4-34.7 | 0:01-0:02, 0:08-0:08, 0:11-0:12, 0:16-0:34, 0:37-0:37, 0:39-0:41 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s06_words_lowq.mp4 | words_lowq | s06.mp4 -> - | 1 -> 0 | 16.4-34.7 |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s07_reupload.mp4 | reupload | s07.mp4 -> s07.mp4 | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s07_lowq.mp4 | lowq | s07.mp4 -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s07_cropped.mp4 | cropped | s07.mp4 -> s07.mp4 | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s07_banner.mp4 | banner | s07.mp4 -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s07_trimmed.mp4 | trimmed | s07.mp4 -> s07.mp4 | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s07_words.mp4 | words | s07.mp4 -> s07.mp4 | 1 -> 1 | 14.3-34.3 | 0:14-0:34 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s07_words_lowq.mp4 | words_lowq | s07.mp4 -> - | 1 -> 0 | 14.3-34.3 |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s08_reupload.mp4 | reupload | s08.mp4 -> s08.mp4 | 0 -> 1 |  | 0:00-0:02, 0:07-0:07, 0:17-0:20, 0:28-0:29, 0:34-0:40 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s08_lowq.mp4 | lowq | s08.mp4 -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s08_cropped.mp4 | cropped | s08.mp4 -> s08.mp4 | 0 -> 1 |  | 0:00-0:02, 0:07-0:07, 0:17-0:20, 0:28-0:29, 0:34-0:40 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s08_banner.mp4 | banner | s08.mp4 -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| s08_trimmed.mp4 | trimmed | s08.mp4 -> s08.mp4 | 0 -> 1 |  | 0:06-0:07, 0:12-0:16, 0:18-0:26, 0:28-0:30, 0:32-0:34 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s08_words.mp4 | words | s08.mp4 -> s08.mp4 | 1 -> 1 | 15.9-34.5 | 0:01-0:02, 0:11-0:12, 0:14-0:33, 0:42-0:43 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s08_words_lowq.mp4 | words_lowq | s08.mp4 -> - | 1 -> 0 | 15.9-34.5 |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| nosrc_01.mp4 | no_source | - -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| nosrc_02.mp4 | no_source | - -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| nosrc_03.mp4 | no_source | - -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| nosrc_04.mp4 | no_source | - -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| nosrc_05.mp4 | no_source | - -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| nosrc_06.mp4 | no_source | - -> - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |

## Failures and causes (written by hand after the run above; a re-run overwrites this file)

- **False "changed words" on unchanged clips (17).** Whisper small does not read the same speech the same way after a re-encode or a different start point. English: one word each (`we'll` / `we will`, `DMAT` / `Digmat`, `client's` / `clients'`, `shows` / `There's`) on s01_trimmed, s03 reupload/cropped/trimmed, s05 reupload/cropped. Hindi (s02, s04, s06, s08): the transcripts are garbled and come out spelled differently each time; s02's source transcript also repeats one Part 3 line in a loop, and s04's has one junk token over 11.8-26 s. Not a clip problem (the clips were checked by waveform: outside the replaced span they are the original sound, correlation 0.999-1.000) and not a matcher bug. Each one becomes CONTRADICTS, which breaks the project's "no false contradiction" rule for video. Not tuned away here: a tolerance for near-identical words would also hide real one-word changes.
- **Low quality (360p, CRF 36) and banner (red bar over the bottom 20%): source not found, 0/8 each.** Match share 0.00-0.10 against 0.6 needed: the frame-embedding match (cosine >= 0.96) does not survive this much damage. They fail safe as NO_RECORD, never MATCHES. This also hides the change in all 8 `_words_lowq` clips.
- **s04_cropped: source not found** (share 0.45 < 0.6). Fails safe as NO_RECORD.
- **Changed span.** English `_words` clips report the replaced span within about 1 s (s03 0:14-0:29, s05 0:12-0:24, s07 0:14-0:34; s01 adds a stray 0:36). Hindi ones add stray ranges outside the span, so the strict "every range within 2 s" check fails for them.
- **No-source clips (6/6 NO_RECORD)** are the generated DEV clips (slides and a synthetic voice), because no unrelated clips were recorded. They are easy negatives; a same-speaker unrelated clip (the hard case) was not tested.
