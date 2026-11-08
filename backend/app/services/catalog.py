"""Read-only queries over the DSA topic catalog and its prerequisite graph."""

import heapq
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Topic, TopicPrerequisite
from app.schemas.catalog import TopicOut, Violation
from app.services.errors import NotFoundError, ValidationFailedError


@dataclass(frozen=True)
class _Graph:
    topics: dict[str, Topic]
    prereqs: dict[str, list[str]]  # slug -> direct prerequisite slugs, sorted by order_index

    def sort_key(self, slug: str) -> tuple[int, str]:
        return (self.topics[slug].order_index, slug)


def _load(db: Session) -> _Graph:
    topics = {t.slug: t for t in db.scalars(select(Topic))}
    by_id = {t.id: t.slug for t in topics.values()}
    prereqs: dict[str, list[str]] = {slug: [] for slug in topics}
    for link in db.scalars(select(TopicPrerequisite)):
        prereqs[by_id[link.topic_id]].append(by_id[link.prerequisite_topic_id])
    graph = _Graph(topics=topics, prereqs=prereqs)
    for slug in prereqs:
        prereqs[slug].sort(key=graph.sort_key)
    return graph


def list_topics(db: Session) -> list[TopicOut]:
    graph = _load(db)
    return [
        TopicOut(
            slug=t.slug,
            name=t.name,
            category=t.category,
            order_index=t.order_index,
            default_problem_count=t.default_problem_count,
            est_minutes_per_problem=t.est_minutes_per_problem,
            difficulty_tier=t.difficulty_tier,
            prerequisites=graph.prereqs[t.slug],
        )
        for t in sorted(graph.topics.values(), key=lambda t: (t.order_index, t.slug))
    ]


def prerequisites(db: Session, slug: str) -> list[str]:
    """Direct prerequisites of `slug`, ordered by order_index."""
    graph = _load(db)
    if slug not in graph.topics:
        raise NotFoundError(f"unknown topic '{slug}'", {"slug": slug})
    return list(graph.prereqs[slug])


def topological_order(db: Session, slugs: list[str]) -> list[str]:
    """Reorder `slugs` so in-set prerequisites come first (Kahn; ties by order_index, slug)."""
    graph = _load(db)
    unknown = [s for s in slugs if s not in graph.topics]
    if unknown:
        raise NotFoundError(f"unknown topic '{unknown[0]}'", {"slugs": unknown})
    if len(set(slugs)) != len(slugs):
        dupes = sorted({s for s in slugs if slugs.count(s) > 1})
        raise ValidationFailedError("duplicate topics in list", {"slugs": dupes})

    wanted = set(slugs)
    indegree = {s: 0 for s in slugs}
    dependants: dict[str, list[str]] = {s: [] for s in slugs}
    for s in slugs:
        for p in graph.prereqs[s]:
            if p in wanted:
                indegree[s] += 1
                dependants[p].append(s)

    ready = [graph.sort_key(s) for s in slugs if indegree[s] == 0]
    heapq.heapify(ready)
    result: list[str] = []
    while ready:
        _, slug = heapq.heappop(ready)
        result.append(slug)
        for d in dependants[slug]:
            indegree[d] -= 1
            if indegree[d] == 0:
                heapq.heappush(ready, graph.sort_key(d))
    if len(result) != len(slugs):  # only possible if the stored graph has a cycle
        raise ValidationFailedError("prerequisite cycle among topics", {"slugs": slugs})
    return result


def validate_order(
    db: Session, slugs: list[str], already_completed: frozenset[str] = frozenset()
) -> list[Violation]:
    """Every violation of catalog order in `slugs` (empty list = valid)."""
    graph = _load(db)
    violations: list[Violation] = []
    seen: set[str] = set()
    for slug in slugs:
        if slug not in graph.topics:
            violations.append(
                Violation(code="UNKNOWN_TOPIC", slug=slug, message=f"unknown topic '{slug}'")
            )
            continue
        if slug in seen:
            violations.append(
                Violation(
                    code="DUPLICATE_TOPIC", slug=slug, message=f"topic '{slug}' appears twice"
                )
            )
            continue
        for p in graph.prereqs[slug]:
            if p not in seen and p not in already_completed:
                violations.append(
                    Violation(
                        code="PREREQUISITE_VIOLATION",
                        slug=slug,
                        prerequisite=p,
                        message=f"'{slug}' requires '{p}' first",
                    )
                )
        seen.add(slug)
    return violations
