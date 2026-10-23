"""Formats, templates and synthetic data agree with docs/formats and the ReBIT transcription."""

import json
import random
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SYN = ROOT / "data" / "synthetic"


def run(script):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script)], capture_output=True, text=True, encoding="utf-8"
    )


def test_format_examples_validate():
    r = run("validate_formats.py")
    assert r.returncode == 0 and "validated 4/4 examples" in r.stdout, r.stdout


def test_templates_cover_every_reason_code():
    r = run("check_templates.py")
    assert r.returncode == 0 and "en: 0 missing" in r.stdout and "hi: 0 missing" in r.stdout, r.stdout


def test_ten_random_portfolios_match_rebit_schema():
    schema = json.loads((ROOT / "data" / "schemas" / "rebit_equities_v1.0.0.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    files = sorted((SYN / "portfolios").glob("P*.json"))
    assert len(files) >= 300
    accounts = 0
    for f in random.Random(0).sample(files, 10):
        case = json.loads(f.read_text(encoding="utf-8"))
        assert case["mock"] is True
        for depo in case["depositories"].values():
            for acc in depo["accounts"]:
                errors = [e.message for e in validator.iter_errors(acc)]
                assert not errors, (f.name, errors)
                accounts += 1
    assert accounts > 0


def test_partial_failure_cases_never_expect_contradicts():
    for f in (SYN / "portfolios").glob("P*.json"):
        case = json.loads(f.read_text(encoding="utf-8"))
        if any(d["status"] == "FAILED" for d in case["depositories"].values()):
            assert all(e["outcome"] != "CONTRADICTS" for e in case["expected"]), f.name


def test_ledger_and_registry_are_mock():
    ledger = json.loads((SYN / "ledger.json").read_text(encoding="utf-8"))
    registry = json.loads((SYN / "suspect_registry_mock.json").read_text(encoding="utf-8"))
    assert ledger["mock"] is True and registry["mock"] is True
    assert len(ledger["injected_customers"]) >= 30
