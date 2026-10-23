import pytest

from app import main, trigger
from app.connectors import footage_index, suspect_registry
from app.evidence import hashchain, pack


@pytest.fixture(autouse=True)
def runtime_in_tmp(tmp_path, monkeypatch):
    """Tests never read or write the demo's runtime state in data/runtime/ (approvals, acks, evidence, events)."""
    monkeypatch.setattr(suspect_registry, "ADDITIONS", tmp_path / "suspect_registry_additions.json")
    monkeypatch.setattr(trigger, "ACKS", tmp_path / "trigger_acks.json")
    monkeypatch.setattr(hashchain, "DB", tmp_path / "kasauti.db")
    monkeypatch.setattr(hashchain, "KEY_FILE", tmp_path / "evidence.key")
    monkeypatch.setattr(pack, "PACKS", tmp_path / "packs")
    monkeypatch.setattr(footage_index, "RESULTS", tmp_path / "video")
    monkeypatch.setattr(main, "EVENTS", tmp_path / "events.jsonl")
