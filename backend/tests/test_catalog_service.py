import pytest
from sqlalchemy.orm import Session

from app.services.catalog import list_topics, prerequisites, topological_order, validate_order
from app.services.errors import NotFoundError, ValidationFailedError


def test_prerequisite_violation(seeded: Session) -> None:
    violations = validate_order(seeded, ["sliding-window", "arrays"])
    assert len(violations) == 1
    v = violations[0]
    assert v.code == "PREREQUISITE_VIOLATION"
    assert (v.slug, v.prerequisite) == ("sliding-window", "arrays")


def test_valid_order(seeded: Session) -> None:
    assert validate_order(seeded, ["arrays", "sliding-window"]) == []


def test_already_completed_satisfies_prerequisites(seeded: Session) -> None:
    done = frozenset({"queues", "recursion"})
    assert validate_order(seeded, ["graphs-bfs-dfs"], already_completed=done) == []
    assert len(validate_order(seeded, ["graphs-bfs-dfs"])) == 2


def test_unknown_and_duplicate_all_reported(seeded: Session) -> None:
    violations = validate_order(seeded, ["arrays", "nope", "arrays", "graphs-bfs-dfs"])
    codes = [(v.code, v.slug, v.prerequisite) for v in violations]
    assert codes == [
        ("UNKNOWN_TOPIC", "nope", None),
        ("DUPLICATE_TOPIC", "arrays", None),
        ("PREREQUISITE_VIOLATION", "graphs-bfs-dfs", "queues"),
        ("PREREQUISITE_VIOLATION", "graphs-bfs-dfs", "recursion"),
    ]


def test_topological_order_is_deterministic(seeded: Session) -> None:
    expected = ["queues", "recursion", "graphs-bfs-dfs"]
    assert topological_order(seeded, ["graphs-bfs-dfs", "recursion", "queues"]) == expected
    assert topological_order(seeded, ["recursion", "graphs-bfs-dfs", "queues"]) == expected
    assert topological_order(seeded, ["sliding-window", "graphs-bfs-dfs", "arrays"]) == [
        "arrays",
        "sliding-window",
        "graphs-bfs-dfs",
    ]


def test_topological_order_errors(seeded: Session) -> None:
    with pytest.raises(NotFoundError):
        topological_order(seeded, ["arrays", "nope"])
    with pytest.raises(ValidationFailedError):
        topological_order(seeded, ["arrays", "arrays"])


def test_prerequisites(seeded: Session) -> None:
    assert prerequisites(seeded, "graphs-bfs-dfs") == ["queues", "recursion"]
    assert prerequisites(seeded, "arrays") == []
    with pytest.raises(NotFoundError):
        prerequisites(seeded, "unknown")


def test_list_topics_sorted(seeded: Session) -> None:
    topics = list_topics(seeded)
    assert [t.slug for t in topics] == [
        "arrays",
        "sliding-window",
        "queues",
        "recursion",
        "graphs-bfs-dfs",
    ]
    assert topics[-1].prerequisites == ["queues", "recursion"]
