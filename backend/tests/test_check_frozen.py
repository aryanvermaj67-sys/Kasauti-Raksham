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
