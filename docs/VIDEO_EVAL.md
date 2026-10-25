# Video evaluation: own test set made by the team, not independent

Run 25 Oct 2026 06:54, device cuda, 62 clips: `python scripts/video_eval.py data/media/clips/labels.csv`

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
- seconds per clip: source search median 0.94, max 1.31; whole check (with transcript) median 3.15, max 11.60

## Per clip

| clip | type | source exp -> got | signal | changed exp -> got | span exp (s) | span got | verdict | reason |
|---|---|---|---|---|---|---|---|---|
| s01_reupload.mp4 | reupload | s01.mp4 -> s01.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s01_lowq.mp4 | lowq | s01.mp4 -> s01.mp4 | audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s01_cropped.mp4 | cropped | s01.mp4 -> s01.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s01_banner.mp4 | banner | s01.mp4 -> s01.mp4 | audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s01_trimmed.mp4 | trimmed | s01.mp4 -> s01.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s01_words.mp4 | words | s01.mp4 -> s01.mp4 | visual + audio_fingerprint | 1 -> 1 | 13.6-31.8 | 0:13-0:31 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s01_words_lowq.mp4 | words_lowq | s01.mp4 -> s01.mp4 | audio_fingerprint | 1 -> 1 | 13.6-31.8 | 0:13-0:31 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s02_reupload.mp4 | reupload | s02.mp4 -> s02.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s02_lowq.mp4 | lowq | s02.mp4 -> s02.mp4 | audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s02_cropped.mp4 | cropped | s02.mp4 -> s02.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s02_banner.mp4 | banner | s02.mp4 -> s02.mp4 | audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s02_trimmed.mp4 | trimmed | s02.mp4 -> s02.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s02_words.mp4 | words | s02.mp4 -> s02.mp4 | visual + audio_fingerprint | 1 -> 1 | 13.8-30.4 | 0:13-0:30 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s02_words_lowq.mp4 | words_lowq | s02.mp4 -> s02.mp4 | audio_fingerprint | 1 -> 1 | 13.8-30.4 | 0:13-0:30 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s03_reupload.mp4 | reupload | s03.mp4 -> s03.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s03_lowq.mp4 | lowq | s03.mp4 -> s03.mp4 | audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s03_cropped.mp4 | cropped | s03.mp4 -> s03.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s03_banner.mp4 | banner | s03.mp4 -> s03.mp4 | audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s03_trimmed.mp4 | trimmed | s03.mp4 -> s03.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s03_words.mp4 | words | s03.mp4 -> s03.mp4 | visual + audio_fingerprint | 1 -> 1 | 14.2-30.2 | 0:14-0:30 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s03_words_lowq.mp4 | words_lowq | s03.mp4 -> s03.mp4 | audio_fingerprint | 1 -> 1 | 14.2-30.2 | 0:14-0:30 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s04_reupload.mp4 | reupload | s04.mp4 -> s04.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s04_lowq.mp4 | lowq | s04.mp4 -> s04.mp4 | audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s04_cropped.mp4 | cropped | s04.mp4 -> s04.mp4 | audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s04_banner.mp4 | banner | s04.mp4 -> s04.mp4 | audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s04_trimmed.mp4 | trimmed | s04.mp4 -> s04.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s04_words.mp4 | words | s04.mp4 -> s04.mp4 | visual + audio_fingerprint | 1 -> 1 | 15.1-30.8 | 0:15-0:31 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s04_words_lowq.mp4 | words_lowq | s04.mp4 -> s04.mp4 | audio_fingerprint | 1 -> 1 | 15.1-30.8 | 0:15-0:31 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s05_reupload.mp4 | reupload | s05.mp4 -> s05.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s05_lowq.mp4 | lowq | s05.mp4 -> s05.mp4 | audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s05_cropped.mp4 | cropped | s05.mp4 -> s05.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s05_banner.mp4 | banner | s05.mp4 -> s05.mp4 | audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s05_trimmed.mp4 | trimmed | s05.mp4 -> s05.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s05_words.mp4 | words | s05.mp4 -> s05.mp4 | visual + audio_fingerprint | 1 -> 1 | 11.8-24.9 | 0:11-0:26 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s05_words_lowq.mp4 | words_lowq | s05.mp4 -> s05.mp4 | audio_fingerprint | 1 -> 1 | 11.8-24.9 | 0:11-0:26 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s06_reupload.mp4 | reupload | s06.mp4 -> s06.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s06_lowq.mp4 | lowq | s06.mp4 -> s06.mp4 | audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s06_cropped.mp4 | cropped | s06.mp4 -> s06.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s06_banner.mp4 | banner | s06.mp4 -> s06.mp4 | audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s06_trimmed.mp4 | trimmed | s06.mp4 -> s06.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s06_words.mp4 | words | s06.mp4 -> s06.mp4 | visual + audio_fingerprint | 1 -> 1 | 16.4-34.7 | 0:16-0:36 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s06_words_lowq.mp4 | words_lowq | s06.mp4 -> s06.mp4 | audio_fingerprint | 1 -> 1 | 16.4-34.7 | 0:16-0:36 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s07_reupload.mp4 | reupload | s07.mp4 -> s07.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s07_lowq.mp4 | lowq | s07.mp4 -> s07.mp4 | audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s07_cropped.mp4 | cropped | s07.mp4 -> s07.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s07_banner.mp4 | banner | s07.mp4 -> s07.mp4 | audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s07_trimmed.mp4 | trimmed | s07.mp4 -> s07.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s07_words.mp4 | words | s07.mp4 -> s07.mp4 | visual + audio_fingerprint | 1 -> 1 | 14.3-34.3 | 0:14-0:34 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s07_words_lowq.mp4 | words_lowq | s07.mp4 -> s07.mp4 | audio_fingerprint | 1 -> 1 | 14.3-34.3 | 0:14-0:34 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s08_reupload.mp4 | reupload | s08.mp4 -> s08.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s08_lowq.mp4 | lowq | s08.mp4 -> s08.mp4 | audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s08_cropped.mp4 | cropped | s08.mp4 -> s08.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s08_banner.mp4 | banner | s08.mp4 -> s08.mp4 | audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s08_trimmed.mp4 | trimmed | s08.mp4 -> s08.mp4 | visual + audio_fingerprint | 0 -> 0 |  |  | MATCHES | ENDORSEMENT_SOURCE_SAME |
| s08_words.mp4 | words | s08.mp4 -> s08.mp4 | visual + audio_fingerprint | 1 -> 1 | 15.9-34.5 | 0:15-0:34, 0:35-0:36 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| s08_words_lowq.mp4 | words_lowq | s08.mp4 -> s08.mp4 | audio_fingerprint | 1 -> 1 | 15.9-34.5 | 0:15-0:34, 0:35-0:36 | CONTRADICTS | ENDORSEMENT_WORDS_CHANGED |
| nosrc_01.mp4 | no_source | - -> - | - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| nosrc_02.mp4 | no_source | - -> - | - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| nosrc_03.mp4 | no_source | - -> - | - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| nosrc_04.mp4 | no_source | - -> - | - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| nosrc_05.mp4 | no_source | - -> - | - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |
| nosrc_06.mp4 | no_source | - -> - | - | 0 -> 0 |  |  | NO_RECORD | ENDORSEMENT_NO_SOURCE |

## Before and after (branch video-robust, written by hand after the run above; a re-run overwrites this file)

| clip type | n | source found before → after | signal after | change found (altered) before → after | false "changed words" before → after |
|---|---|---|---|---|---|
| reupload | 8 | 8 → 8 | visual + audio 8 | | 6 → 0 |
| lowq (360p, CRF 36) | 8 | 0 → 8 | audio 8 | | 0 → 0 |
| cropped | 8 | 7 → 8 | visual + audio 7, audio 1 | | 5 → 0 |
| banner | 8 | 0 → 8 | audio 8 | | 0 → 0 |
| trimmed | 8 | 8 → 8 | visual + audio 8 | | 6 → 0 |
| words | 8 | 8 → 8 | visual + audio 8 | 8 → 8 | |
| words_lowq | 8 | 0 → 8 | audio 8 | 0 → 8 | |
| no_source | 6 | NO_RECORD 6 → 6 | none | | |

Before = commit 8bb34cb (Whisper word diff decides; CLIP frames only). Span within 2 s of the labelled window: 3/16 → 14/16, median edge error 0.6 s.

## What changed

- **Changed words are decided from the audio, never from transcripts.** Once the source and offset are known, 64-band log-mel frames (60 Hz-3.8 kHz) of the upload and the source are scaled by the source's band statistics, the upload's level/EQ is removed per band (median over frames the fingerprint proved unchanged), and the two are aligned (per-frame offsets from the fingerprint, or a +-1 s lag search after a visual-only match, then DTW in a +-0.2 s band). A span is "changed" only when the 0.5 s running median of the frame distance stays above FLOOR for at least MIN_RUN_S. Whisper only quotes the words inside flagged spans. No flagged span = no "words changed" claim, whatever the transcripts say, so Hindi transcription noise cannot raise one.
- **Second source signal: audio fingerprint** (peak-pair landmark hashes of the 90 Hz-5 kHz spectrogram; a source needs FP_MIN_HITS hashes agreeing on one offset). Source found = visual OR fingerprint; when both fire on different clips, no source (picture of one recording, sound of another). When the picture finds a clip, the fingerprint is asked about that clip first.
- **Splices of a different length**: each upload frame takes the offset of its nearest fingerprint hit, so audio after a longer or shorter replacement still lines up and only the splice is flagged.

## Calibration (scripts/calibrate_audio.py; source clips only, never the altered clips)

64 re-encodes of the 8 sources (AAC 32k mono, AAC 48k, MP3 64k, 8 kHz and 22.05 kHz resample, 6 dB quieter, 6 dB louder, first 5 s cut), 123,184 frames:
- smoothed distance median 0.033, 99th percentile 0.179, 99.9th 0.205, max 0.240 → **FLOOR = 0.205**; longest run above it 0.52 s → **MIN_RUN_S = 1.02 s** (+0.5 s).
- fingerprint: best score of a source re-encode against the OTHER 7 sources (different statements, same speakers and room) 4; lowest score against its own source 1,023 → **FP_MIN_HITS = 8** (2 x 4).
- the 3.8 kHz band limit also comes from this run: with bands to 7.6 kHz an 8 kHz resample alone reached distance 0.92.

## Why the 360p copies found no source (tests/test_video_lowq_cause.py)

Not frame sampling, aspect or scaling: a 360p copy at CRF 18 has same-time CLIP cosine >= 0.99 to the source (s05: 0.997). Heavy compression is the cause: CRF 36 alone gives 0.959-0.981 by clip, CRF 36 at 360p 0.907-0.961, so fewer than 60 % of frames reach the 0.96 cut-off. The cut-off was not lowered; the audio fingerprint finds these clips instead. pHash survives compression (distance 0/64) but was not used: two moments 10 s apart in the same talking-head clip are only 2/64 apart, so it cannot pin an offset and would also match another statement filmed in the same room.

## Limits and open points

- **No same-speaker, unrelated-words clips (N01/N02) were recorded**, so the hard no-source case is not tested directly. The nearest test: every source against the other 7 (same speakers, same room, different statements) scores at most 4 fingerprint hits against a threshold of 8 and an own-source minimum of 1,023.
- **s08 spans count as misses only because of the label.** labels.csv marks where the new speech plays (to 34.5 s), but the clip builder muted the original until Part 3 (40.8 s), so the audio really differs to 40.8 s; the extra flag at 0:35-0:36 is a muted original word. Against the muted window all 16 spans fit. labels.csv was not edited.
- **Muted words are under-detected when the source has gated silence**: s08's source has digital silence in its pauses, so in a muted stretch only the word frames differ and the 0.5 s running median falls to 0 between them; its "हिम्मत रखें" line (37.8-40 s) is not flagged.
- **Audio that is bit-identical to an indexed clip is found by sound** even under another picture. The dev clips share template sentences in one synthetic voice, so "unindexed" dev_new_1 contains about 20 s of dev_02's exact recording and is now found by the fingerprint (it was NO_RECORD before); the dev test was changed to say so. The message for that case ("the original video exists, but the words were changed") says "video" where only the sound was re-used.
- No lip-sync or deepfake analysis of any kind: these checks compare an upload with a known recording.
