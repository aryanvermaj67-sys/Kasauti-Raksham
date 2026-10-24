"""scripts/run_frozen.py: refuses a tampered set; the EXAMPLE rule cases, brokers and payees go through the rules."""

import importlib.util
import shutil

from tests.helpers import ROOT

spec = importlib.util.spec_from_file_location("run_frozen", ROOT / "scripts" / "run_frozen.py")
run_frozen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_frozen)
EXAMPLE = ROOT / "data" / "frozen_example"


def test_refuses_a_tampered_set(tmp_path, capsys):
    root = tmp_path / "frozen"
    shutil.copytree(EXAMPLE, root)
    (root / "payees.json").write_text((root / "payees.json").read_text(encoding="utf-8") + " ", encoding="utf-8")
    assert run_frozen.main([str(root), "--example"]) == 2
    out = capsys.readouterr().out
    print(out)
    assert "REFUSED" in out and "payees.json changed since HASH.txt" in out


def test_example_rule_items_through_the_rules_without_touching_the_set():
    before = run_frozen.check_frozen.hash_lines(EXAMPLE)
    items = run_frozen.rule_items(EXAMPLE)
    for i in items:
        print(i["kind"], i["id"], i["expected"], i["got"], i["expected_reason"], i["got_reason"])
    assert {i["kind"] for i in items} == {"rule_case", "rule_summary", "broker", "payee"}
    assert all(i["ok"] for i in items)
    assert run_frozen.check_frozen.hash_lines(EXAMPLE) == before


def test_partial_coverage_case_is_never_a_contradiction():
    case = {"claims": [{"id": "c1", "type": "holding", "fields": {"instrument_name": "Infosys", "isin": "INE009A01021",
            "quantity": 8000, "value_inr": None}}], "consent_scope": ["CDSL", "NSDL"],
            "depositories": [{"depository": "CDSL", "status": "OK", "accounts": []},
                             {"depository": "NSDL", "status": "FAILED"}]}  # fmt: skip
    v = run_frozen.through_rules(case, case["claims"])[0]["c1"]
    assert (v.outcome, v.reason_code) == ("NO_RECORD", "HOLDING_PARTIAL_COVERAGE")
