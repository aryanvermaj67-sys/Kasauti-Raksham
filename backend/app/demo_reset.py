"""Demo reset: wipe runtime state (evidence, dev key, MOCK registry additions, acks, events) back to the seed."""

import shutil

from app import main, reviewer, trigger
from app.connectors import footage_index, suspect_registry
from app.evidence import hashchain, pack


def counts() -> dict:
    events = main.EVENTS.read_text(encoding="utf-8").count("\n") if main.EVENTS.exists() else 0
    return {
        "evidence checks": len(hashchain.checks()) if hashchain.DB.exists() else 0,
        "reviewer queue": len(reviewer.queue()) if hashchain.DB.exists() else 0,
        "registry seed entries (mock)": len(suspect_registry._entries()),
        "registry additions (mock)": len(suspect_registry._additions()),
        "trigger acks": len(trigger._acks()),
        "events logged": events,
        "dev key file": int(hashchain.KEY_FILE.exists()),
    }


def reset() -> None:
    for f in (hashchain.DB, hashchain.KEY_FILE, suspect_registry.ADDITIONS, trigger.ACKS, main.EVENTS):
        f.unlink(missing_ok=True)
    for d in (pack.PACKS, footage_index.RESULTS):
        shutil.rmtree(d, ignore_errors=True)
