from typing import Any

import pytest
from fastapi.testclient import TestClient
from freezegun import freeze_time

from app.config import get_settings

WEEK = {"mon": 120, "tue": 120, "wed": 90, "thu": 120, "fri": 60, "sat": 240, "sun": 240}
FULL_PATCH: dict[str, Any] = {
    "name": "Niya Ganesh",
    "goal_text": "Finish core DSA before placement season",
    "target_date": "2027-01-31",
    "skill_level": "intermediate",
    "weekly_availability": WEEK,
}


def _patch(client: TestClient, body: dict[str, Any]) -> Any:
    return client.patch("/api/profile", json=body)


def _field_locs(response: Any) -> list[str]:
    return [".".join(str(p) for p in e["loc"][1:]) for e in response.json()["detail"]]


def test_first_get_creates_profile(client: TestClient) -> None:
    r = client.get("/api/profile")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == 1
    assert body["name"] == ""
    assert body["timezone"] == get_settings().app_timezone_fallback
    assert body["weekly_availability"] == dict.fromkeys(WEEK, 0)
    assert body["checkin_time"] == "21:00"
    assert body["reminder_time"] == "22:30"
    assert body["preferences"] == {}
    assert body["is_complete"] is False
    assert body["missing_fields"] == ["name", "target_date", "skill_level", "weekly_availability"]


@freeze_time("2026-11-08 12:00:00")
def test_full_patch_then_repeat(client: TestClient) -> None:
    r = _patch(client, FULL_PATCH)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["profile"]["is_complete"] is True
    assert body["profile"]["missing_fields"] == []
    assert body["changed_fields"] == [
        "goal_text",
        "name",
        "skill_level",
        "target_date",
        "weekly_availability",
    ]
    assert body["plan_impact"] == {
        "availability_or_deadline_changed": True,
        "active_plan_now_invalid": False,
        "violations": [],
    }
    first_updated = body["profile"]["updated_at"]

    again = _patch(client, FULL_PATCH).json()
    assert again["changed_fields"] == []
    assert again["plan_impact"]["availability_or_deadline_changed"] is False
    assert again["profile"]["updated_at"] == first_updated


def test_name_is_stripped_and_changed_fields_only_real_changes(client: TestClient) -> None:
    r = _patch(client, {"name": "  Niya  ", "checkin_time": "21:00"})
    assert r.status_code == 200
    assert r.json()["profile"]["name"] == "Niya"
    assert r.json()["changed_fields"] == ["name"]
    assert r.json()["plan_impact"]["availability_or_deadline_changed"] is False


@pytest.mark.parametrize(
    ("week", "loc"),
    [
        ({k: v for k, v in WEEK.items() if k != "sun"}, "weekly_availability"),
        ({**WEEK, "xyz": 10}, "weekly_availability"),
        ({**WEEK, "mon": 721}, "weekly_availability.mon"),
        ({**WEEK, "mon": -1}, "weekly_availability.mon"),
        ({**WEEK, "mon": 1.5}, "weekly_availability.mon"),
        (dict.fromkeys(WEEK, 0), "weekly_availability"),
    ],
)
def test_invalid_availability(client: TestClient, week: dict[str, Any], loc: str) -> None:
    r = _patch(client, {"weekly_availability": week})
    assert r.status_code == 422
    assert loc in _field_locs(r)


def test_invalid_timezone(client: TestClient) -> None:
    r = _patch(client, {"timezone": "Mars/Base"})
    assert r.status_code == 422
    assert "timezone" in _field_locs(r)


def test_valid_timezone(client: TestClient) -> None:
    r = _patch(client, {"timezone": "Europe/London"})
    assert r.status_code == 200
    assert r.json()["profile"]["timezone"] == "Europe/London"


@freeze_time("2026-06-15 20:00:00")  # 20:00 UTC = 01:30 on 16 June in Asia/Kolkata
def test_target_date_uses_profile_timezone(client: TestClient) -> None:
    r = _patch(client, {"timezone": "Asia/Kolkata", "target_date": "2026-06-14"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_FAILED"
    assert r.json()["error"]["details"] == {"field": "target_date"}

    # Still 15 June in UTC, but already 16 June in Kolkata -> 15 June is yesterday there.
    assert (
        _patch(client, {"timezone": "Asia/Kolkata", "target_date": "2026-06-15"}).status_code == 422
    )
    assert _patch(client, {"timezone": "UTC", "target_date": "2026-06-15"}).status_code == 200
    # Stored timezone (UTC now) is used when the patch has none.
    assert _patch(client, {"target_date": "2026-06-15"}).status_code == 200


def test_reminder_must_follow_checkin(client: TestClient) -> None:
    r = _patch(client, {"checkin_time": "22:00", "reminder_time": "21:30"})
    assert r.status_code == 422
    assert r.json() == {
        "ok": False,
        "error": {
            "code": "VALIDATION_FAILED",
            "message": "reminder_time must be later than checkin_time on the same day",
            "details": {"field": "reminder_time"},
        },
    }
    assert _patch(client, {"checkin_time": "21:00", "reminder_time": "21:00"}).status_code == 422
    assert _patch(client, {"reminder_time": "00:30"}).status_code == 422  # no crossing midnight
    # Merged with stored reminder_time 22:30
    assert _patch(client, {"checkin_time": "23:00"}).status_code == 422
    assert _patch(client, {"checkin_time": "20:00", "reminder_time": "20:45"}).status_code == 200


@pytest.mark.parametrize("value", ["25:00", "9:00", "21:60", "2100", ""])
def test_bad_time_format(client: TestClient, value: str) -> None:
    r = _patch(client, {"reminder_time": value})
    assert r.status_code == 422
    assert "reminder_time" in _field_locs(r)


def test_nulls(client: TestClient) -> None:
    r = _patch(client, {"name": None})
    assert r.status_code == 422
    assert "name" in _field_locs(r)
    for field in ("timezone", "weekly_availability", "checkin_time", "preferences"):
        assert _patch(client, {field: None}).status_code == 422

    assert _patch(client, {"goal_text": "something"}).status_code == 200
    r = _patch(client, {"goal_text": None})
    assert r.status_code == 200
    assert r.json()["profile"]["goal_text"] is None
    assert r.json()["changed_fields"] == ["goal_text"]


def test_unknown_field_rejected(client: TestClient) -> None:
    r = _patch(client, {"favourite_colour": "blue"})
    assert r.status_code == 422


def test_other_field_rules(client: TestClient) -> None:
    assert _patch(client, {"name": "   "}).status_code == 422
    assert _patch(client, {"name": "x" * 101}).status_code == 422
    assert _patch(client, {"goal_text": "x" * 1001}).status_code == 422
    assert _patch(client, {"skill_level": "guru"}).status_code == 422
    assert _patch(client, {"preferred_session_minutes": 14}).status_code == 422
    assert _patch(client, {"preferred_session_minutes": 721}).status_code == 422
    assert _patch(client, {"preferences": {f"k{i}": i for i in range(51)}}).status_code == 422
    assert _patch(client, {"preferences": ["not", "a", "dict"]}).status_code == 422

    r = _patch(client, {"preferences": {"language": "python"}, "preferred_session_minutes": 45})
    assert r.status_code == 200
    r = _patch(client, {"preferences": {"theme": "dark"}})
    assert r.json()["profile"]["preferences"] == {"theme": "dark"}  # full replacement
