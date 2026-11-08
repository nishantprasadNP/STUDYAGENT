import json
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.models import Topic, TopicPrerequisite
from app.seed.__main__ import main
from app.seed.loader import CatalogError, load_catalog, seed
from tests.conftest import FIXTURES_DIR

VALID = FIXTURES_DIR / "catalog_valid.json"


def _counts(db: Session) -> tuple[int, int]:
    topics = db.scalar(select(func.count()).select_from(Topic)) or 0
    links = db.scalar(select(func.count()).select_from(TopicPrerequisite)) or 0
    return topics, links


def _write(tmp_path: Path, data: dict[str, Any]) -> Path:
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(data))
    return path


def _valid_data() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(VALID.read_text())
    return data


def test_seed_is_idempotent(db_session: Session) -> None:
    catalog = load_catalog(VALID)
    first = seed(db_session, catalog)
    assert (first.inserted, first.updated, first.unchanged) == (5, 0, 0)
    assert first.prerequisite_links == 3
    counts = _counts(db_session)
    assert counts == (5, 3)

    second = seed(db_session, catalog)
    assert (second.inserted, second.updated, second.unchanged) == (0, 0, 5)
    assert _counts(db_session) == counts


def test_changed_field_counts_as_updated(db_session: Session, tmp_path: Path) -> None:
    seed(db_session, load_catalog(VALID))
    data = _valid_data()
    data["topics"][0]["default_problem_count"] = 99
    report = seed(db_session, load_catalog(_write(tmp_path, data)))
    assert (report.inserted, report.updated, report.unchanged) == (0, 1, 4)
    arrays = db_session.scalars(select(Topic).where(Topic.slug == "arrays")).one()
    assert arrays.default_problem_count == 99


def test_removed_prerequisite_link_is_deleted(db_session: Session, tmp_path: Path) -> None:
    seed(db_session, load_catalog(VALID))
    data = _valid_data()
    graphs = next(t for t in data["topics"] if t["slug"] == "graphs-bfs-dfs")
    graphs["prerequisites"] = ["recursion"]
    report = seed(db_session, load_catalog(_write(tmp_path, data)))
    assert report.prerequisite_links == 2
    assert _counts(db_session) == (5, 2)


def test_removed_topic_is_kept_and_reported(db_session: Session, tmp_path: Path) -> None:
    seed(db_session, load_catalog(VALID))
    data = _valid_data()
    data["topics"] = [t for t in data["topics"] if t["slug"] != "sliding-window"]
    report = seed(db_session, load_catalog(_write(tmp_path, data)))
    assert report.orphaned == ["sliding-window"]
    assert _counts(db_session)[0] == 5


def test_cycle_fails_and_writes_nothing(db_session: Session) -> None:
    with pytest.raises(CatalogError) as exc_info:
        load_catalog(FIXTURES_DIR / "catalog_cycle.json")
    assert any(e.startswith("cycle: a -> b -> c -> a") for e in exc_info.value.errors)
    assert _counts(db_session) == (0, 0)


def test_unknown_prerequisite_names_both_slugs() -> None:
    with pytest.raises(CatalogError) as exc_info:
        load_catalog(FIXTURES_DIR / "catalog_unknown_prereq.json")
    assert "unknown prerequisite 'queues' in topic 'graphs-bfs-dfs'" in exc_info.value.errors


def test_duplicate_slug_fails() -> None:
    with pytest.raises(CatalogError) as exc_info:
        load_catalog(FIXTURES_DIR / "catalog_duplicate_slug.json")
    assert "duplicate slug 'arrays'" in exc_info.value.errors


def test_all_errors_collected(tmp_path: Path) -> None:
    data = _valid_data()
    data["topics"].append(dict(data["topics"][0]))  # duplicate arrays
    data["topics"][1]["prerequisites"] = ["arrays", "nope"]
    with pytest.raises(CatalogError) as exc_info:
        load_catalog(_write(tmp_path, data))
    assert len(exc_info.value.errors) == 2


def test_empty_catalog_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(CatalogError) as exc_info:
        load_catalog(_write(tmp_path, {"topics": []}))
    assert exc_info.value.errors == ["catalog has no topics"]


def test_field_errors_reported(tmp_path: Path) -> None:
    data = _valid_data()
    data["topics"][0]["slug"] = "Bad Slug"
    data["topics"][1]["difficulty_tier"] = 4
    with pytest.raises(CatalogError) as exc_info:
        load_catalog(_write(tmp_path, data))
    joined = "\n".join(exc_info.value.errors)
    assert "topics.0.slug" in joined
    assert "topics.1.difficulty_tier" in joined


def test_dry_run_writes_nothing(db_session: Session) -> None:
    report = seed(db_session, load_catalog(VALID), dry_run=True)
    assert report.inserted == 5
    assert _counts(db_session) == (0, 0)


def test_cli_exit_codes(
    session_factory: sessionmaker[Session], capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["--file", str(VALID)], session_factory=session_factory) == 0
    out = capsys.readouterr().out
    assert "inserted=5 updated=0 unchanged=0 prerequisite_links=3 orphaned=0" in out

    assert main(["--file", str(VALID)], session_factory=session_factory) == 0
    assert "inserted=0 updated=0 unchanged=5" in capsys.readouterr().out

    code = main(
        ["--file", str(FIXTURES_DIR / "catalog_cycle.json")], session_factory=session_factory
    )
    assert code == 1
    assert "ERROR cycle: a -> b -> c -> a" in capsys.readouterr().err


def test_cli_dry_run(session_factory: sessionmaker[Session]) -> None:
    assert main(["--file", str(VALID), "--dry-run"], session_factory=session_factory) == 0
    with session_factory() as db:
        assert _counts(db) == (0, 0)


def test_cli_warns_about_orphans(
    session_factory: sessionmaker[Session], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    main(["--file", str(VALID)], session_factory=session_factory)
    data = _valid_data()
    data["topics"] = [t for t in data["topics"] if t["slug"] not in {"queues", "graphs-bfs-dfs"}]
    capsys.readouterr()
    assert main(["--file", str(_write(tmp_path, data))], session_factory=session_factory) == 0
    out = capsys.readouterr().out
    assert "WARNING: in DB but not in file (kept): graphs-bfs-dfs, queues" in out
