"""scripts/check_frozen.py: the EXAMPLE set passes; a missing field, a wrong count and a tampered file each fail."""

import importlib.util
import json
import shutil

import pytest

from tests.helpers import ROOT

SCRIPT = ROOT / "scripts" / "check_frozen.py"
spec = importlib.util.spec_from_file_location("check_frozen", SCRIPT)
check_frozen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_frozen)


@pytest.fixture
def example(tmp_path):
    root = tmp_path / "frozen"
    shutil.copytree(ROOT / "data" / "frozen_example", root)
    return root


def run(root, capsys):
    code = check_frozen.main([str(root), "--example"])
    out = capsys.readouterr().out
    print(out)
    return code, out


def test_example_passes_and_only_hash_is_written(example, capsys):
    (example / "HASH.txt").unlink()
    before = check_frozen.hash_lines(example)
    code, out = run(example, capsys)
    assert code == 0 and "wrote HASH.txt" in out and "FROZEN SET OK" in out
    assert check_frozen.hash_lines(example) == before  # nothing but HASH.txt changed
    assert run(example, capsys)[0] == 0  # second run verifies the hash it wrote


def test_missing_field_fails(example, capsys):
    brokers = json.loads((example / "brokers.json").read_text(encoding="utf-8"))
    del brokers[0]["expected_reason_code"]
    (example / "brokers.json").write_text(json.dumps(brokers), encoding="utf-8")
    code, out = run(example, capsys)
    assert code == 1 and "brokers[0]: missing field(s) expected_reason_code" in out


def test_wrong_count_fails(example, capsys):
    payees = json.loads((example / "payees.json").read_text(encoding="utf-8"))
    (example / "payees.json").write_text(json.dumps(payees[:1]), encoding="utf-8")
    code, out = run(example, capsys)
    assert code == 1 and "count: payees 1, need at least 2" in out


def test_tampered_file_fails(example, capsys):
    png = example / "screenshots" / "ex_s1.png"
    data = bytearray(png.read_bytes())
    data[-20] ^= 1
    png.write_bytes(bytes(data))
    code, out = run(example, capsys)
    assert code == 1 and "hash: screenshots/ex_s1.png changed since HASH.txt" in out


def test_full_spec_minimums_reject_the_example(example, capsys):
    code = check_frozen.main([str(example)])
    out = capsys.readouterr().out
    assert code == 1 and "count: rule_cases 2, need at least 100" in out and "coverage: reason codes" in out


def test_checker_never_reads_the_rules():
    src = SCRIPT.read_text(encoding="utf-8")
    assert "rules.py" not in src and "from app" not in src and "import app" not in src


# no-video scope (docs/FROZEN_SET_SPEC.md, "No-video scope")
def no_clips(root):
    """An example set whose videos folder holds an empty manifest and no clips, and that has no HASH.txt yet."""
    (root / "HASH.txt").unlink()
    for clip in (root / "videos").iterdir():
        clip.unlink()
    (root / "videos" / "manifest.json").write_text("[]", encoding="utf-8")


def skip_run(root, capsys, *flags):
    code = check_frozen.main([str(root), "--example", *flags])
    out = capsys.readouterr().out
    print(out)
    return code, out


def test_no_video_passes_with_an_empty_videos_folder_and_is_honoured_without_the_flag(example, capsys):
    no_clips(example)
    code, out = skip_run(example, capsys, "--skip-videos")
    assert code == 0 and "scope: no-video" in out and "skip videos" in out
    assert (example / "HASH.txt").read_text(encoding="utf-8").splitlines()[0] == "scope: no-video"
    code, out = skip_run(example, capsys)  # no flag: the first line of HASH.txt decides
    assert code == 0 and "scope: no-video" in out and "FROZEN SET OK" in out


def test_plain_mode_still_fails_without_clips(example, capsys):
    no_clips(example)
    (example / "videos" / "manifest.json").write_text(
        (ROOT / "data" / "frozen_example" / "videos" / "manifest.json").read_text(encoding="utf-8"), encoding="utf-8"
    )
    code, out = skip_run(example, capsys)
    assert code == 1 and "clip file not found in videos/" in out and "scope: full" in out
    assert not (example / "HASH.txt").exists()


def test_no_video_still_checks_the_manifest_shape(example, capsys):
    no_clips(example)
    (example / "videos" / "manifest.json").write_text('[{"file": "a.mp4"}]', encoding="utf-8")
    code, out = skip_run(example, capsys, "--skip-videos")
    assert code == 1 and "missing field(s) expected_source, expected_changed, variant" in out


def test_tampered_or_added_file_is_refused_under_no_video_scope(example, capsys):
    no_clips(example)
    assert skip_run(example, capsys, "--skip-videos")[0] == 0
    png = example / "screenshots" / "ex_s1.png"
    original = png.read_bytes()
    data = bytearray(original)
    data[-20] ^= 1
    png.write_bytes(bytes(data))
    code, out = skip_run(example, capsys)
    assert code == 1 and "hash: screenshots/ex_s1.png changed since HASH.txt" in out
    png.write_bytes(original)
    (example / "videos" / "v001.mp4").write_bytes(b"late clip")
    code, out = skip_run(example, capsys)
    assert code == 1 and "hash: videos/v001.mp4 added after HASH.txt" in out


def test_a_full_scope_hash_cannot_be_weakened_by_the_flag(example, capsys):
    code, out = skip_run(example, capsys, "--skip-videos")  # the example set is hashed with full scope
    assert code == 1 and "HASH.txt is full scope" in out


def test_run_frozen_honours_the_scope_and_lists_videos_as_not_run(example, capsys, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "cache")  # importing run_frozen sets a default otherwise
    spec_rf = importlib.util.spec_from_file_location("run_frozen", ROOT / "scripts" / "run_frozen.py")
    run_frozen = importlib.util.module_from_spec(spec_rf)
    spec_rf.loader.exec_module(run_frozen)
    no_clips(example)
    (example / "videos" / "manifest.json").write_text(
        '[{"file": "v001.mp4", "expected_source": null, "expected_changed": false, "variant": "none"}]',
        encoding="utf-8",
    )
    assert skip_run(example, capsys, "--skip-videos")[0] == 0
    problems, _ = run_frozen.gate(example, True)
    assert problems == []
    text = "\n".join(run_frozen.video_section(example, True))
    assert "v001.mp4`: not run (no-video scope)" in text
