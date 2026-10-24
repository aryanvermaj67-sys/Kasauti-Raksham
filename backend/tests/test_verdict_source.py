"""Verdicts come only from verdict/rules.py: no other module builds one; no route or frontend file hard-codes one."""

import ast

from fastapi.testclient import TestClient

from app import main
from app.verdict import rules
from tests.helpers import ROOT, TEMPLATES

APP = ROOT / "backend" / "app"
OUTCOMES = {"MATCHES", "CONTRADICTS", "NO_RECORD"}
REASONS = set(TEMPLATES["en"])


def test_no_backend_module_but_rules_builds_a_verdict():
    found = []
    for path in APP.rglob("*.py"):
        rel = path.relative_to(APP).as_posix()
        if rel in ("verdict/rules.py", "schemas/verdict.py"):  # the rules, and the type that lists the outcomes
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        compared = {id(c) for n in ast.walk(tree) if isinstance(n, ast.Compare) for c in [n.left, *n.comparators]}
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and getattr(n.func, "id", getattr(n.func, "attr", "")) in ("Verdict", "Message"):
                found.append(f"{rel}:{n.lineno} builds {ast.unparse(n.func)}(...)")
            if isinstance(n, ast.Constant) and n.value in OUTCOMES | REASONS and id(n) not in compared:
                found.append(f"{rel}:{n.lineno} literal {n.value!r}")
    print("\n" + "\n".join(found or ["no verdict built or hard-coded outside verdict/rules.py"]))
    assert not found


def test_every_verdict_in_the_api_response_was_made_by_rules(monkeypatch):
    made = []
    real = rules._v

    def spy(*a, **kw):
        made.append(real(*a, **kw))
        return made[-1]

    monkeypatch.setattr(rules, "_v", spy)  # rules' single constructor; the router can only pass its output on
    monkeypatch.setenv("LLM_PROVIDER", "cache")
    client = TestClient(main.app)
    shot = (ROOT / "data" / "demo_cache" / "demo-001.png").read_bytes()
    claimset = client.post("/api/read", files={"file": ("d.png", shot, "image/png")}).json()
    body = {"claimset": claimset, "customer_id": "SYN-C0001", "consent_id": "consent-mock-1"}
    verdicts = client.post("/api/check", json=body).json()["verdicts"]
    print(f"\n{len(verdicts)} verdicts in the response, {len(made)} made by rules._v")
    assert verdicts and [v.model_dump(mode="json") for v in made] == verdicts


def test_frontend_never_sets_an_outcome_or_reason_code():
    bad = []
    for path in (ROOT / "frontend" / "src").rglob("*.ts*"):
        code = path.read_text(encoding="utf-8")
        for reason in REASONS:
            if f"'{reason}'" in code or f'"{reason}"' in code:
                bad.append(f"{path.name}: reason code {reason}")
        for outcome in OUTCOMES:
            for quoted in (f"outcome: '{outcome}'", f'outcome: "{outcome}"', f"outcome = '{outcome}'"):
                if quoted in code:
                    bad.append(f"{path.name}: sets {quoted}")
    print("\n" + "\n".join(bad or ["frontend: outcomes are read from the API (compared, never set); no reason codes"]))
    assert not bad
