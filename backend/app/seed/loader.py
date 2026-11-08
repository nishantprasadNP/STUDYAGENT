"""Parse, validate and upsert the DSA catalog JSON."""

import json
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Topic, TopicPrerequisite
from app.schemas.catalog import CatalogFile, CatalogTopicIn

BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = BACKEND_DIR / "seed" / "dsa_catalog.json"

_TOPIC_FIELDS = (
    "name",
    "category",
    "order_index",
    "default_problem_count",
    "est_minutes_per_problem",
    "difficulty_tier",
)


class CatalogError(Exception):
    """The catalog file is unusable. `errors` lists every problem found."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors


@dataclass
class SeedReport:
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    prerequisite_links: int = 0
    orphaned: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"inserted={self.inserted} updated={self.updated} unchanged={self.unchanged} "
            f"prerequisite_links={self.prerequisite_links} orphaned={len(self.orphaned)}"
        )


def _format_pydantic(exc: ValidationError) -> list[str]:
    out = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err["loc"])
        msg = err["msg"].removeprefix("Value error, ")
        out.append(f"{loc}: {msg}" if loc else msg)
    return out


def _find_cycles(topics: list[CatalogTopicIn]) -> list[list[str]]:
    """DFS over topic -> prerequisite edges; returns each distinct cycle found."""
    edges = {t.slug: t.prerequisites for t in topics}
    state: dict[str, int] = {}  # 1 = on stack, 2 = done
    stack: list[str] = []
    cycles: list[list[str]] = []
    seen_cycles: set[frozenset[str]] = set()

    def visit(slug: str) -> None:
        state[slug] = 1
        stack.append(slug)
        for nxt in edges.get(slug, []):
            if nxt not in edges:
                continue  # unknown prerequisite, reported separately
            if state.get(nxt) == 1:
                cycle = [*stack[stack.index(nxt) :], nxt]
                key = frozenset(cycle)
                if key not in seen_cycles:
                    seen_cycles.add(key)
                    cycles.append(cycle)
            elif nxt not in state:
                visit(nxt)
        stack.pop()
        state[slug] = 2

    for t in topics:
        if t.slug not in state:
            visit(t.slug)
    return cycles


def validate_catalog(catalog: CatalogFile) -> list[str]:
    """File-level checks. Returns every error (empty = valid)."""
    errors: list[str] = []
    counts: dict[str, int] = {}
    for t in catalog.topics:
        counts[t.slug] = counts.get(t.slug, 0) + 1
    errors.extend(f"duplicate slug '{s}'" for s, n in counts.items() if n > 1)
    for t in catalog.topics:
        errors.extend(
            f"unknown prerequisite '{p}' in topic '{t.slug}'"
            for p in t.prerequisites
            if p not in counts
        )
    errors.extend("cycle: " + " -> ".join(c) for c in _find_cycles(catalog.topics))
    return errors


def load_catalog(path: Path) -> CatalogFile:
    """Parse and fully validate a catalog file. Raises CatalogError listing all problems."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CatalogError([f"file not found: {path}"]) from exc
    except json.JSONDecodeError as exc:
        raise CatalogError([f"invalid JSON: {exc}"]) from exc
    try:
        catalog = CatalogFile.model_validate(raw)
    except ValidationError as exc:
        raise CatalogError(_format_pydantic(exc)) from exc
    errors = validate_catalog(catalog)
    if errors:
        raise CatalogError(errors)
    return catalog


def seed(db: Session, catalog: CatalogFile, dry_run: bool = False) -> SeedReport:
    """Upsert topics + prerequisite links in one transaction. Never deletes topics."""
    errors = validate_catalog(catalog)
    if errors:
        raise CatalogError(errors)

    report = SeedReport()
    try:
        existing = {t.slug: t for t in db.scalars(select(Topic))}
        file_slugs = {t.slug for t in catalog.topics}

        for item in catalog.topics:
            row = existing.get(item.slug)
            if row is None:
                row = Topic(slug=item.slug, **{f: getattr(item, f) for f in _TOPIC_FIELDS})
                db.add(row)
                existing[item.slug] = row
                report.inserted += 1
                continue
            changed = False
            for f in _TOPIC_FIELDS:
                if getattr(row, f) != getattr(item, f):
                    setattr(row, f, getattr(item, f))
                    changed = True
            if changed:
                report.updated += 1
            else:
                report.unchanged += 1
        db.flush()

        id_of = {slug: t.id for slug, t in existing.items()}
        current: set[tuple[int, int]] = {
            (link.topic_id, link.prerequisite_topic_id)
            for link in db.scalars(select(TopicPrerequisite))
        }
        file_topic_ids = {id_of[s] for s in file_slugs}
        wanted = {
            (id_of[item.slug], id_of[p]) for item in catalog.topics for p in item.prerequisites
        }
        for topic_id, prereq_id in sorted(wanted - current):
            db.add(TopicPrerequisite(topic_id=topic_id, prerequisite_topic_id=prereq_id))
        for topic_id, prereq_id in sorted(current - wanted):
            if topic_id in file_topic_ids:  # orphaned topics keep their links untouched
                db.delete(db.get_one(TopicPrerequisite, (topic_id, prereq_id)))
        db.flush()

        report.prerequisite_links = len(wanted)
        report.orphaned = sorted(set(existing) - file_slugs)
    except Exception:
        db.rollback()
        raise

    if dry_run:
        db.rollback()
    else:
        db.commit()
    return report
