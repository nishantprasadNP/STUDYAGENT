import pytest
from fastapi.testclient import TestClient

import app.api.health as health_module


def test_health_ok(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "db": "ok",
        "scheduler": "not_started",
        "version": "0.1.0",
    }


def test_health_degraded_when_db_fails(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(health_module, "check_db", lambda _session: False)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["db"] == "error"
