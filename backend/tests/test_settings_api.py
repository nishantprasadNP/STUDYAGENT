from typing import Any

import pytest
from fastapi.testclient import TestClient

DEFAULTS = {
    "behind_completion_threshold": 0.70,
    "behind_carryover_count": 2,
    "ahead_completion_threshold": 1.00,
    "weak_topic_min_problems": 5,
    "weak_topic_solve_ratio": 0.60,
    "weak_topic_difficult_ratio": 0.50,
    "max_daily_overbook_ratio": 1.00,
    "revision_expiry_hours": 24,
    "max_topics_per_day": 2,
    "outstanding_checkin_days": 3,
}


def test_first_get_returns_defaults(client: TestClient) -> None:
    r = client.get("/api/settings")
    assert r.status_code == 200
    body = r.json()
    for key, value in DEFAULTS.items():
        assert body[key] == pytest.approx(value), key


@pytest.mark.parametrize(
    "body",
    [
        {"behind_completion_threshold": 0},
        {"behind_completion_threshold": 1.5},
        {"weak_topic_solve_ratio": -0.1},
        {"max_daily_overbook_ratio": 0},
        {"max_topics_per_day": 0},
        {"revision_expiry_hours": 1.5},
        {"max_topics_per_day": None},
        {"unknown_setting": 1},
    ],
)
def test_invalid_values(client: TestClient, body: dict[str, Any]) -> None:
    assert client.patch("/api/settings", json=body).status_code == 422


def test_cross_field_check(client: TestClient) -> None:
    r = client.patch(
        "/api/settings",
        json={"behind_completion_threshold": 0.9, "ahead_completion_threshold": 0.8},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_FAILED"
    assert r.json()["error"]["details"]["field"] == "behind_completion_threshold"
    # Merged with stored ahead (1.00): fine.
    assert (
        client.patch("/api/settings", json={"behind_completion_threshold": 0.9}).status_code == 200
    )
    # Lowering ahead below stored behind (0.9) fails.
    assert (
        client.patch("/api/settings", json={"ahead_completion_threshold": 0.8}).status_code == 422
    )


def test_valid_patch_persists(client: TestClient) -> None:
    r = client.patch(
        "/api/settings", json={"max_topics_per_day": 3, "max_daily_overbook_ratio": 1.2}
    )
    assert r.status_code == 200
    assert r.json()["max_topics_per_day"] == 3
    assert client.get("/api/settings").json()["max_daily_overbook_ratio"] == pytest.approx(1.2)
