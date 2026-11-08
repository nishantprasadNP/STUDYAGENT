"""DSA catalog schemas: API output, seed-file input, and order violations."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
Slug = Annotated[str, StringConstraints(pattern=SLUG_PATTERN, max_length=64)]


class TopicOut(BaseModel):
    slug: str
    name: str
    category: str
    order_index: int
    default_problem_count: int
    est_minutes_per_problem: int
    difficulty_tier: int
    prerequisites: list[str]


class CatalogTopicIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: Slug
    name: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    category: Annotated[str, StringConstraints(min_length=1, max_length=64)]
    order_index: Annotated[int, Field(strict=True, ge=0)]
    default_problem_count: Annotated[int, Field(strict=True, ge=1)]
    est_minutes_per_problem: Annotated[int, Field(strict=True, ge=1, le=240)]
    difficulty_tier: Annotated[int, Field(strict=True, ge=1, le=3)]
    prerequisites: list[Slug] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_prerequisites(self) -> "CatalogTopicIn":
        if len(set(self.prerequisites)) != len(self.prerequisites):
            raise ValueError(f"topic '{self.slug}' lists a prerequisite more than once")
        if self.slug in self.prerequisites:
            raise ValueError(f"topic '{self.slug}' lists itself as a prerequisite")
        return self


class CatalogFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topics: list[CatalogTopicIn]

    @model_validator(mode="after")
    def _not_empty(self) -> "CatalogFile":
        if not self.topics:
            raise ValueError("catalog has no topics")
        return self


class Violation(BaseModel):
    code: Literal["UNKNOWN_TOPIC", "DUPLICATE_TOPIC", "PREREQUISITE_VIOLATION"]
    slug: str
    prerequisite: str | None = None
    message: str
