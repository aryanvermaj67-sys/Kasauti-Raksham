from fastapi.testclient import TestClient

from app.main import app


def test_health():
    r = TestClient(app).get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "ready": True, "loading": []}  # no lifespan here, so nothing is loading


def test_health_not_ready_while_models_load(monkeypatch):
    from app import main

    monkeypatch.setattr(main, "LOADING", {"video models"})
    assert TestClient(app).get("/api/health").json() == {"status": "ok", "ready": False, "loading": ["video models"]}
