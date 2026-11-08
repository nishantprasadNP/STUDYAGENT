from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_empty_db_returns_empty_list(client: TestClient) -> None:
    r = client.get("/api/topics")
    assert r.status_code == 200
    assert r.json() == []


def test_topics_sorted_with_prerequisites(client: TestClient, seeded: Session) -> None:
    r = client.get("/api/topics")
    assert r.status_code == 200
    body = r.json()
    assert [t["slug"] for t in body] == [
        "arrays",
        "sliding-window",
        "queues",
        "recursion",
        "graphs-bfs-dfs",
    ]
    assert body[0] == {
        "slug": "arrays",
        "name": "Arrays",
        "category": "linear",
        "order_index": 1,
        "default_problem_count": 10,
        "est_minutes_per_problem": 20,
        "difficulty_tier": 1,
        "prerequisites": [],
    }
    assert body[1]["prerequisites"] == ["arrays"]
    assert body[4]["prerequisites"] == ["queues", "recursion"]
